# -*- coding: utf-8 -*-

'''
Created on 06 Juin. 2019

@author: DESTER
'''
import base64

from odoo import fields, models, api, _
from datetime import time, date, timedelta
import time, datetime
from dateutil import parser, relativedelta
import odoo.addons.decimal_precision as dp
from odoo.exceptions import *
#from fpdf import FPDF
import os
#from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter
import json
import logging

_logger = logging.getLogger(__name__)

class AccountTaxReturn(models.TransientModel):
    """
    Model for Tax Return Djibouti
    """

    _name = "account.tax.return.dji"
    _description = "Tax Return"

    current_year = time.localtime().tm_year

    LISTE_YEARS = [
        (current_year - 1, str(current_year - 1)),
        (current_year, str(current_year)),
        (current_year + 1, str(current_year + 1)),
        (current_year + 2, str(current_year + 2)),
        (current_year + 3, str(current_year + 3)),
        (current_year + 4, str(current_year + 4)),
        (current_year + 5, str(current_year + 5)),
    ]

    def _default_name(self):
        return "Liasse fiscale "

    def _default_country(self):
        cnt = None
        country = self.env['res.country'].search([('code','=','DJ')])
        for p in country:
            cnt = p.id
        return cnt


    name = fields.Char(string=_("Liasse Fiscale"), required=True, default=_default_name, help=u"")
    date_start = fields.Date(string=_("Date ouverture Exercice"), required=True, help=u"")
    date_close = fields.Date(string=_("Date cloture Exercice"), required=True, help=u"")
    year = fields.Selection(LISTE_YEARS, string=_("Année"), compute="_compute_yaer", store=True, help=u"Indique l'année N de la liasse fiscale")
    duration = fields.Integer(string=_("Durée (en mois)"), compute="_compute_duration", store=True, help=u"")
    nif = fields.Char(string=_("Numéro d'identification"), help="Indique le numéro NIF de la société")
    secu_number = fields.Char(string=_("Numéro Caisse Social"), compute="_compute_secu_number", store=True,
                              help="Indique le numéro sécurité sociale de la société")
    company_id = fields.Many2one("res.company", string=_("Société"), default=lambda self: self.env.user.company_id,
                                 help=u"")

    country_id = fields.Many2one('res.country', string=_("Pays"),
                                 default=_default_country, help = "")

    # generer liasse fiscal
    is_tax_return_generated = fields.Boolean(string=_("Test Liasse fiscal généré"), default=False, help=u"")
    doc_attachment = fields.Many2one(comodel_name="ir.attachment", string=_("Liasse fiscale"))

    bilan_report_data = fields.Char(string=_("Billan Data"))
    bilan_passif_report_data = fields.Char(string=_("Billan Passif Data"))
    bilan_actif_report_data = fields.Char(string=_("Billan Actif Data"))
    cr_report_data = fields.Char(string=_("Compte de resultat Data"))
    sig_report_data = fields.Char(string=_("Solde Intermediaire de Gestion"))

    list_account_doublon_of_exclude = []
    list_account_inverse = []
    #['7091','7092','7093','7094','7095','7096','7098','6037','6031','6032']
    list_index_stock_delta = ['achat_marchandises_vendues','production_stockee_destockage','matieres_p_approvisionnements_c']
    list_index_acount_plus_moins = ['7091','7092','7093','7094','7095','7096','7098','6037','6031','6032']

    def get_year_n(self):
        return self.year

    def get_year_n_chaine(self):
        return str(self.year)

    def get_year_n_1(self):
        return (self.year - 1)

    def get_date_year_n(self):
        return self.date_close.strftime('%d/%m/%Y')

    def get_date_year_n_1(self):
        return parser.parse(str(self.get_year_n_1())+"-"+str(self.date_close.month)+"-"+str(self.date_close.day)).strftime('%d/%m/%Y')



    # Button imprimer compte resultat
    def button_print_sig(self):
        if self.date_start != False and self.date_close != False:
            self.get_solde_intermediaire_gestion_data()
            return self.env.ref('account_tax_return_dji.tax_return_sig_report').report_action(self.ids)
        else:
            raise Warning(_("Les champs date début et date fin exercice doivent être remplir"))

    # Button imprimer compte resultat
    def button_print_sig_detail(self):
        if self.date_start != False and self.date_close != False:
            self.get_solde_intermediaire_gestion_detail_data()
            return self.env.ref('account_tax_return_dji.tax_return_sig_detail_report').report_action(self.ids)
        else:
            raise Warning(_("Les champs date début et date fin exercice doivent être remplir"))



    # Retourne vrai si l'année passé en paramètre est bissextile
    def bissextile(self, annee):
        annee = int(annee)
        bissextile = False
        if annee % 400 == 0:
            bissextile = True
        elif annee % 100 == 0:
            bissextile = False
        elif annee % 4 == 0:
            bissextile = True
        else:
            bissextile = False
        return bissextile

    # @api.onchange("name", "year")
    # def onchange_name(self):
    #     setting = self.env['res.config.settings'].search([('company_id', '=',
    #                                                        self.env.user.company_id.id)])  # recherche du jour configurer dans les paramètres systeme
    #     month_last_year_fiscal_setting = 12
    #     day_last_year_fiscal_setting = 31
    #     for s in setting:
    #         if s.fiscalyear_last_month != False:
    #             month_last_year_fiscal_setting = s.fiscalyear_last_month
    #         if s.fiscalyear_last_day != False:
    #             day_last_year_fiscal_setting = s.fiscalyear_last_day
    #     self.date_close = str(self.year) + "-" + str(month_last_year_fiscal_setting) + "-" + str(
    #         day_last_year_fiscal_setting)
    #
    #     if self.bissextile(self.year):
    #         self.date_start = (parser.parse(self.date_close.strftime('%Y-%m-%d')) - timedelta(days=(365))).strftime(
    #             '%Y-%m-%d')
    #     else:
    #         self.date_start = (parser.parse(self.date_close.strftime('%Y-%m-%d')) - timedelta(days=(364))).strftime(
    #             '%Y-%m-%d')

    @api.one
    @api.depends("date_close","date_start")
    def _compute_duration(self):
        if self.date_close and self.date_start:
            d2 = parser.parse(self.date_close.strftime('%Y-%m-%d'))
            d1 = parser.parse(self.date_start.strftime('%Y-%m-%d'))
            r = relativedelta.relativedelta(d2, d1)
            self.duration = 1+r.months

    @api.one
    @api.depends("date_close")
    def _compute_yaer(self):
        if self.date_close:
            self.year = str(self.date_close.year)


    # Fonction transformant les données json (chaine de caractère) en list ou dictionnaire
    @api.multi
    def sig_report_data_json_to_list(self):
        self.ensure_one()
        list = []
        return json.loads(self.sig_report_data)

    @api.multi
    def bilan_report_data_json_to_list(self):  # bilan global (actif & passif)
        self.ensure_one()
        list = []
        return json.loads(self.bilan_report_data)

    @api.multi
    def bilan_passif_report_data_json_to_list(self):
        self.ensure_one()
        list = []
        return json.loads(self.bilan_passif_report_data)

    @api.multi
    def bilan_actif_report_data_json_to_list(self):
        self.ensure_one()
        list = []
        return json.loads(self.bilan_actif_report_data)

    @api.multi
    def ft_report_data_json_to_list(self):
        self.ensure_one()
        list = []
        return json.loads(self.sig_report_data)

    # Fonction transformant les données de type list ou dictionnaire en données json (chaine de caractère)
    @api.multi
    def list_to_data_json(self, list_value):
        return json.dumps(list_value)


    def separateur_millier(self, n, sep = "."):
        s = str(n)
        l = len(s)
        d = int(l / 3)
        for i in range(1,d+1):
            s = s[:l-3*i] + sep + s[l-3*i:]
        return s

    def separateur_millier_with_vide(self, n, sep = "."):
        if int(n) == 0:
            return ""
        s = str(int(n))
        l = len(s)
        d = int(l / 3)
        for i in range(1,d+1):
            s = s[:l-3*i] + sep + s[l-3*i:]
        return s

    # Function qui retourne la somme des debit d'une liste de radical de comptes
    @api.one
    def sum_debit(self, radical_account, date_deb, date_fin):
        som = 0
        if radical_account[0] == '_':  # Cas des compte à exclure (compte sauf ..)
            radical_account = radical_account[1:len(radical_account)]
        l = str(radical_account) + "%"
        account_obj = self.env["account.move.line"].search(
            [('account_id', '=like', l), ('date', '>=', date_deb), ('date', '<=', date_fin),
             ('company_id', '=', self.env.user.company_id.id)])
        for acc in account_obj:
            som += acc.debit
        return som

    # Function qui retourne la somme des credit d'une liste de radical de comptes
    @api.one
    def sum_credit(self, radical_account, date_deb, date_fin):
        som = 0
        if radical_account[0] == '_':  # Cas des compte à exclure (compte sauf ..)
            radical_account = radical_account[1:len(radical_account)]
        l = str(radical_account) + "%"
        account_obj = self.env["account.move.line"].search(
            [('account_id', '=like', l), ('date', '>=', date_deb), ('date', '<=', date_fin),
             ('company_id', '=', self.env.user.company_id.id)])
        for acc in account_obj:
            som += acc.credit
        return som

    # Fonction qui retourne le solde (debit-credit)
    # Cas 419 = debit - credit
    @api.one
    def solde_debit_credit(self, list_of_radical_account, date_deb, date_fin):
        solde = 0
        for l in list_of_radical_account:
            if l in self.list_account_doublon_of_exclude:
                if self.get_solde_debit_credit(l, date_deb, date_fin) >= 0:
                    solde = solde + self.sum_debit(l, date_deb, date_fin)[0] - \
                            self.sum_credit(l, date_deb, date_fin)[0]
            else:
                if l in self.list_account_inverse:
                    solde = solde + (
                                self.sum_credit(l, date_deb, date_fin)[0] - self.sum_debit(l, date_deb, date_fin)[
                            0])
                else:
                    if l[0] == '_':
                        if (self.sum_debit(l, date_deb, date_fin)[0] - self.sum_credit(l, date_deb, date_fin)[0]) < 0:
                            solde = solde + abs(self.sum_debit(l, date_deb, date_fin)[0] - self.sum_credit(l, date_deb, date_fin)[0])
                        else:
                            solde = solde - abs(self.sum_debit(l, date_deb, date_fin)[0] - self.sum_credit(l, date_deb, date_fin)[0])
                    else:
                        solde = solde + self.sum_debit(l, date_deb, date_fin)[0] - \
                                self.sum_credit(l, date_deb, date_fin)[0]
        return solde

    ############################### Block COMPTE DE RESULTAT  ##########################################

    def get_vente_marchandise_production(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['vente_marchandise', 'production_vendue']:
                if value.get('signe') == '+':
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    def get_marge_commercial(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['vente_marchandise', 'achat_marchandises_vendues']:
                if value.get('signe') == '+':
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    #égale à la somme +/- des ses elements
    def get_production_exercice(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['production_vendue', 'production_stockee_destockage','production_immobilisee']:
                if value.get('signe') == '+':
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    #égale à (production de l'exercice moins ses eleements)
    def get_marge_brute_production(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['production_vendue', 'production_stockee_destockage','production_immobilisee','matieres_p_approvisionnements_c', 'sous_traitance_direct']:
                if value.get('signe') == '+':
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    #égale à (marge commerciale plus marge brute production)
    def get_marge_brute_global(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['vente_marchandise', 'achat_marchandises_vendues','production_vendue', 'production_stockee_destockage','production_immobilisee','matieres_p_approvisionnements_c', 'sous_traitance_direct']:
                if value.get('signe') == '+':
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    #égale à (marge brute globale +/- ses elements)
    def get_valeur_ajouter(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['vente_marchandise', 'achat_marchandises_vendues','production_vendue', 'production_stockee_destockage','production_immobilisee','matieres_p_approvisionnements_c', 'sous_traitance_direct','autre_achat_charge_externe']:
                if value.get('signe') == '+':
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    #égale (valeur ajouté +/- ses elements)
    def get_excedent_brut_exploitation(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['vente_marchandise', 'achat_marchandises_vendues', 'production_vendue',
                                    'production_stockee_destockage', 'production_immobilisee',
                                    'matieres_p_approvisionnements_c', 'sous_traitance_direct',
                                    'autre_achat_charge_externe','subventions_exploitation',
                                    'impots_taxes_versements_assimile','salaires_du_personnel','charges_sociales_du_personnel']:
                if value.get('signe') == '+':
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    #égale à excedent brute exploitation +/- ses elements)
    def get_resultat_exploitation(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['vente_marchandise', 'achat_marchandises_vendues', 'production_vendue',
                                    'production_stockee_destockage', 'production_immobilisee',
                                    'matieres_p_approvisionnements_c', 'sous_traitance_direct',
                                    'autre_achat_charge_externe','subventions_exploitation',
                                    'impots_taxes_versements_assimile','salaires_du_personnel','charges_sociales_du_personnel',
                                    'autres_produits_gestion_courant','autres_charge_gestion_courant','reprises_amortissements_provisions_t_c',
                                    'dotations_aux_amortissement','dotations_aux_provisions'
                                    ]:
                if value.get('signe') == '+':
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    # égale à resultat exploitation +/- ses elements
    def get_resultat_courant(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['vente_marchandise', 'achat_marchandises_vendues', 'production_vendue',
                                    'production_stockee_destockage', 'production_immobilisee',
                                    'matieres_p_approvisionnements_c', 'sous_traitance_direct',
                                    'autre_achat_charge_externe', 'subventions_exploitation',
                                    'impots_taxes_versements_assimile', 'salaires_du_personnel',
                                    'charges_sociales_du_personnel',
                                    'autres_produits_gestion_courant', 'autres_charge_gestion_courant',
                                    'reprises_amortissements_provisions_t_c',
                                    'dotations_aux_amortissement', 'dotations_aux_provisions',
                                    'quotes_parts_resultat_operations_commun','produits_financier','charges_financieres'
                                    ]:
                if value.get('signe') == '+':
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    #égale à la somme +/- ses elements
    def get_resultat_exceptionel(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['produits_exceptionnels','charges_exceptionnels'
                                    ]:
                if value.get('signe') == '+':
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    # égale à (resultat courant +/- resultat exceptionnel)
    def get_resultat_net(self, data_list_all):
        som = 0
        som_n_1 = 0
        for value in data_list_all:
            if value.get('ref') in ['G_RCO','G_REX','impot_sur_benefice','participation_salarier' ]:
                if value.get('signe') in ['+','g']:
                    som = som + value.get('solde_n')
                    som_n_1 = som_n_1 + value.get('solde_n_1')
                else:
                    som = som - value.get('solde_n')
                    som_n_1 = som_n_1 - value.get('solde_n_1')
        return {'som_n': som, 'som_n_1': som_n_1}

    # Permet de retourner le signe du solde
    def get_signe_line(self, solde):

        if solde < 0:
            return "-"
        else:
            return "+"

    # Permet de retourner le signe du solde connaissant son radical compte
    def get_signe_account_line(self, index, solde):
        # if index in self.list_index_stock_delta:
        return self.get_signe_line(-1 * solde)

    def test_(self):
        som1 = 12
        som2 = 20
        return {'som1': som1, 'som2': som2}

    #Calcul le solde intermediaire globale
    @api.one
    def get_solde_intermediaire_gestion_data(self):
        sig_data = []
        list_account_value = [
            {'list_G_VMP': ['g', 'Vente  marchandises + Production', 't_g0'],
             'list_vente_marchandise': ['+', "vente de marchandises", 'g1', '707', '7097'],
             'list_achat_marchandises_vendues': ['-/+', "Coût d'achat des marchandises vendues", 'g1', '6037', '607','608', '6097'],
             'list_G_MC': ['g', 'Marge Commerçiale', 't_g1'],
             'list_production_vendue': ['+', "Production vendue", 'g2', '701', '702', '703', '704', '705', '706', '708', '709', '_7097'],
             'list_production_stockee_destockage': ['-/+', "Production stockée ou déstockag", 'g2', '713'],
             'list_production_immobilisee': ['+', "Production immobilisé", 'g2', '72'],
             'list_G_PE': ['g', "Production de l'exercice", 't_g2'],
             'list_matieres_p_approvisionnements_c': ['-/+', "Matières premières, approvisionnements consommés", 'g3','601', '602', '6031', '6032', '609', '_6097'],
             'list_sous_traitance_direct': ['-', "Sous traitance direct", 'g3', '604', '605'],
             'list_G_MBP': ['g', "Marge brute de production", 't_g3'],
             'list_G_MBG': ['g', "Marge brute globale", 't_g4'],
             'list_autre_achat_charge_externe': ['-', "Autres achats + charges externes", 'g5', '606', '610', '611','612', '613', '614', '615', '616', '617', '618', '619', '621',
                                                 '622', '623', '624', '625', '626', '627', '628', '629'],
             'list_G_VA': ['g', "Valeur Ajoutée", 't_g5'],
             'list_subventions_exploitation': ['+', "Subventions d'exploitation", 'g6', '74'],
             'list_impots_taxes_versements_assimile': ['-', "Impôts, taxes et versements assimilé", 'g6', '63'],
             'list_salaires_du_personnel': ['-', "Salaires du personnel", 'g6', '641'],
             'list_charges_sociales_du_personnel': ['-', "Charges sociales du personnel", 'g6', '644', '645', '646',
                                                    '647', '648', '649'],
             'list_G_EBE': ['g', "Excédent brut d'exploitation", 't_g6'],
             'list_autres_produits_gestion_courant': ['+', "Autres produits de gestion courant", 'g7', '75'],
             'list_autres_charge_gestion_courant': ['-', "Autres charges de gestion courant", 'g7', '65'],
             'list_reprises_amortissements_provisions_t_c': ['+',
                                                             "Reprises amortissements provisions, transferts de charge",
                                                             'g7', '781', '791'],
             'list_dotations_aux_amortissement': ['-', "Dotations aux amortissements", 'g7', '6811', '6812', '6868'],
             'list_dotations_aux_provisions': ['-', "Dotations aux provisions", 'g7', '6875', '6815'],
             'list_G_REP': ['g', "Résultat d'exploitation", 't_g7'],
             'list_quotes_parts_resultat_operations_commun': ['+', "Quotes parts de résultat sur opérations en commun",
                                                              'g8', '755'],
             'list_produits_financier': ['+', "Produits financier", 'g8', '76', '786', '796'],
             'list_charges_financieres': ['-', "Charges financières", 'g8', '66', '686'],
             'list_G_RCO': ['g', "Résultat courant", 't_g8'],
             'list_produits_exceptionnels': ['+', "Produits Exceptionnels", 'g9', '77', '787', '797'],
             'list_charges_exceptionnels': ['-', "Charges Exceptionnels", 'g9', '67', '687'],
             'list_G_REX': ['g', "Résultat exceptionnel", 't_g9'],
             'list_impot_sur_benefice': ['-', "Impôt sur les bénéfices", 'g10', '695'],
             'list_participation_salarier': ['-', "Participation des salariés", 'g10', '691'],
             'list_G_RNE': ['g', "Résultat Net", 't_g10'],
             }
        ]

        list_account = list_account_value[0]
        date_start_n = self.date_start
        date_close_n = self.date_close
        date_start_n_moins_1 = (parser.parse(date_start_n.strftime('%Y-%m-%d')) - timedelta(days=(365))).strftime('%Y-%m-%d')
        date_close_n_moins_1 = (parser.parse(date_close_n.strftime('%Y-%m-%d')) - timedelta(days=(365))).strftime('%Y-%m-%d')
        for ref in list_account:
            solde_n = self.solde_debit_credit(list_account.get(ref)[3:len(list_account.get(ref))], date_start_n, date_close_n)[0]
            solde_n_moins_1 = self.solde_debit_credit(list_account.get(ref)[3:len(list_account.get(ref))], date_start_n_moins_1,date_close_n_moins_1)[0]
            if list_account.get(ref)[0] in ['+', '-']:
                sig_data.append({'signe': list_account.get(ref)[0], 'ref':ref[5:len(ref)],'libelle': list_account.get(ref)[1],'groupe': list_account.get(ref)[2],
                                 'solde_n': round(abs(solde_n)), 'taux_n':0.0,'solde_n_1': round(abs(solde_n_moins_1)),
                                 'taux_n_1':0.0,'ecart_n_n1':(round(abs(solde_n)) - round(abs(solde_n_moins_1))),
                                 'taux_ecart_n_n1':0.0
                                })
            if list_account.get(ref)[0] in ['-/+']:
                sig_data.append({'signe': self.get_signe_account_line(ref[5:len(ref)],solde_n), 'ref':ref[5:len(ref)],'libelle': list_account.get(ref)[1],'groupe': list_account.get(ref)[2],
                                 'solde_n': round(abs(solde_n)), 'taux_n':0.0,'solde_n_1': round(abs(solde_n_moins_1)),
                                 'taux_n_1':0.0,'ecart_n_n1':(round(abs(solde_n)) - round(abs(solde_n_moins_1))),
                                 'taux_ecart_n_n1':0.0
                                })
            if list_account.get(ref)[0] not in ['+', '-','-/+']:
                sig_data.append({'signe': list_account.get(ref)[0], 'ref':ref[5:len(ref)], 'libelle': list_account.get(ref)[1],
                                 'groupe': list_account.get(ref)[2],
                                 'solde_n': 0.0, 'taux_n': 0.0, 'solde_n_1': 0.0,
                                 'taux_n_1': 0.0, 'ecart_n_n1': 0.0,
                                 'taux_ecart_n_n1': 0.0
                                 })
        self.sig_report_data = self.list_to_data_json(sig_data)
        sig_data_list = self.sig_report_data_json_to_list()
        #Calcul des lignes globaux
        for sig in sig_data_list:
            if sig.get('ref') == "G_VMP":
                val = self.get_vente_marchandise_production(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),'ecart_n_n1': (val.get('som_n')- val.get('som_n_1')) })
            if sig.get('ref') == "G_MC":
                val = self.get_marge_commercial(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'), 'ecart_n_n1': (val.get('som_n')- val.get('som_n_1'))})
            if sig.get('ref') == "G_PE":
                val = self.get_production_exercice(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'), 'ecart_n_n1': (val.get('som_n')- val.get('som_n_1'))})
            if sig.get('ref') == "G_MBP":
                val = self.get_marge_brute_production(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'), 'ecart_n_n1': (val.get('som_n')- val.get('som_n_1'))})
            if sig.get('ref') == "G_MBG":
                val = self.get_marge_brute_global(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'), 'ecart_n_n1': (val.get('som_n')- val.get('som_n_1'))})
            if sig.get('ref') == "G_VA":
                val = self.get_valeur_ajouter(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'), 'ecart_n_n1': (val.get('som_n')- val.get('som_n_1'))})
            if sig.get('ref') == "G_EBE":
                val = self.get_excedent_brut_exploitation(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'), 'ecart_n_n1': (val.get('som_n')- val.get('som_n_1'))})
            if sig.get('ref') == "G_REP":
                val = self.get_resultat_exploitation(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'), 'ecart_n_n1': (val.get('som_n')- val.get('som_n_1'))})
            if sig.get('ref') == "G_RCO":
                val = self.get_resultat_courant(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'), 'ecart_n_n1': (val.get('som_n')- val.get('som_n_1'))})
            if sig.get('ref') == "G_REX":
                val = self.get_resultat_exceptionel(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'), 'ecart_n_n1': (val.get('som_n')- val.get('som_n_1'))})
            if sig.get('ref') == "G_RNE":
                val = self.get_resultat_net(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'), 'ecart_n_n1': (val.get('som_n')- val.get('som_n_1'))})

        self.sig_report_data = self.list_to_data_json(sig_data_list)
        # sig_data_list = self.sig_report_data_json_to_list()

        return {}


    def get_account_libelle(self, account_code):
        nm=""
        ac = self.env['account.account'].search([('code','=like',account_code)])
        for a in ac:
            nm = a.name
        return nm


    # Calcul le solde intermediaire detail
    @api.one
    def get_solde_intermediaire_gestion_detail_data(self):
        sig_data = []
        list_account_value = [
            {'list_G_VMP': ['g', 'Vente  marchandises + Production', 't_g0'],
             'list_vente_marchandise': ['+', "vente de marchandises", 'g1', '707', '7097'],
             'list_achat_marchandises_vendues': ['-/+', "Coût d'achat des marchandises vendues", 'g1', '6037', '607',
                                                 '608', '6097'],
             'list_G_MC': ['g', 'Marge Commerçiale', 't_g1'],
             'list_production_vendue': ['+', "Production vendue", 'g2', '701', '702', '703', '704', '705', '706', '708',
                                        '709', '_7097'],
             'list_production_stockee_destockage': ['-/+', "Production stockée ou déstockag", 'g2', '713'],
             'list_production_immobilisee': ['+', "Production immobilisé", 'g2', '72'],
             'list_G_PE': ['g', "Production de l'exercice", 't_g2'],
             'list_matieres_p_approvisionnements_c': ['-', "Matières premières, approvisionnements consommés", 'g3',
                                                      '601', '602', '6031', '6032', '609', '_6097'],
             'list_sous_traitance_direct': ['-', "Sous traitance direct", 'g3', '604', '605'],
             'list_G_MBP': ['g', "Marge brute de production", 't_g3'],
             'list_G_MBG': ['g', "Marge brute globale", 't_g4'],
             'list_autre_achat_charge_externe': ['-', "Autres achats + charges externes", 'g5', '606', '610', '611',
                                                 '612', '613', '614', '615', '616', '617', '618', '619', '621',
                                                 '622', '623', '624', '625', '626', '627', '628', '629'],
             'list_G_VA': ['g', "Valeur Ajoutée", 't_g5'],
             'list_subventions_exploitation': ['+', "Subventions d'exploitation", 'g6', '74'],
             'list_impots_taxes_versements_assimile': ['-', "Impôts, taxes et versements assimilé", 'g6', '63'],
             'list_salaires_du_personnel': ['-', "Salaires du personnel", 'g6', '641'],
             'list_charges_sociales_du_personnel': ['-', "Charges sociales du personnel", 'g6', '644', '645', '646',
                                                    '647', '648', '649'],
             'list_G_EBE': ['g', "Excédent brut d'exploitation", 't_g6'],
             'list_autres_produits_gestion_courant': ['+', "Autres produits de gestion courant", 'g7', '75'],
             'list_autres_charge_gestion_courant': ['-', "Autres charges de gestion courant", 'g7', '65'],
             'list_reprises_amortissements_provisions_t_c': ['+',
                                                             "Reprises amortissements provisions, transferts de charge",
                                                             'g7', '781', '791'],
             'list_dotations_aux_amortissement': ['-', "Dotations aux amortissements", 'g7', '6811', '6812', '6868'],
             'list_dotations_aux_provisions': ['-', "Dotations aux provisions", 'g7','6875', '6815'], 
             'list_G_REP': ['g', "Résultat d'exploitation", 't_g7'],
             'list_quotes_parts_resultat_operations_commun': ['+', "Quotes parts de résultat sur opérations en commun",
                                                              'g8', '755'],
             'list_produits_financier': ['+', "Produits financier", 'g8', '76', '786', '796'],
             'list_charges_financieres': ['-', "Charges financières", 'g8', '66', '686'],
             'list_G_RCO': ['g', "Résultat courant", 't_g8'],
             'list_produits_exceptionnels': ['+', "Produits Exceptionnels", 'g9', '77', '787', '797'],
             'list_charges_exceptionnels': ['-', "Charges Exceptionnels", 'g9', '67', '687'],
             'list_G_REX': ['g', "Résultat exceptionnel", 't_g9'],
             'list_impot_sur_benefice': ['-', "Impôt sur les bénéfices", 'g10', '695'],
             'list_participation_salarier': ['-', "Participation des salariés", 'g10', '691'],
             'list_G_RNE': ['g', "Résultat Net", 't_g10'],
             }
        ]

        list_account = list_account_value[0]
        date_start_n = self.date_start
        date_close_n = self.date_close
        date_start_n_moins_1 = (parser.parse(date_start_n.strftime('%Y-%m-%d')) - timedelta(days=(365))).strftime(
            '%Y-%m-%d')
        date_close_n_moins_1 = (parser.parse(date_close_n.strftime('%Y-%m-%d')) - timedelta(days=(365))).strftime(
            '%Y-%m-%d')
        for ref in list_account:
            #Obtenir liste ligne global
            solde_n = self.solde_debit_credit(list_account.get(ref)[3:len(list_account.get(ref))], date_start_n, date_close_n)[0]
            solde_n_moins_1 = self.solde_debit_credit(list_account.get(ref)[3:len(list_account.get(ref))], date_start_n_moins_1,date_close_n_moins_1)[0]
            if list_account.get(ref)[0] in ['+', '-']:
                sig_data.append(
                    {'signe': list_account.get(ref)[0], 'ref': ref[5:len(ref)], 'libelle': list_account.get(ref)[1].upper(),
                     'groupe': list_account.get(ref)[2],
                     'solde_n': round(abs(solde_n)), 'taux_n': 0.0, 'solde_n_1': round(abs(solde_n_moins_1)),
                     'taux_n_1': 0.0, 'ecart_n_n1': (round(abs(solde_n)) - round(abs(solde_n_moins_1))),
                     'taux_ecart_n_n1': 0.0
                     })
            if list_account.get(ref)[0] in ['-/+']:
                sig_data.append({'signe': self.get_signe_account_line(ref[5:len(ref)], solde_n), 'ref': ref[5:len(ref)],
                                 'libelle': list_account.get(ref)[1].upper(), 'groupe': list_account.get(ref)[2],
                                 'solde_n': round(abs(solde_n)), 'taux_n': 0.0,
                                 'solde_n_1': round(abs(solde_n_moins_1)),
                                 'taux_n_1': 0.0, 'ecart_n_n1': (round(abs(solde_n)) - round(abs(solde_n_moins_1))),
                                 'taux_ecart_n_n1': 0.0
                                 })
            if list_account.get(ref)[0] not in ['+', '-', '-/+']:
                sig_data.append(
                    {'signe': list_account.get(ref)[0], 'ref': ref[5:len(ref)], 'libelle': list_account.get(ref)[1].upper(),
                     'groupe': list_account.get(ref)[2],
                     'solde_n': 0.0, 'taux_n': 0.0, 'solde_n_1': 0.0,
                     'taux_n_1': 0.0, 'ecart_n_n1': 0.0,
                     'taux_ecart_n_n1': 0.0
                     })
            solde_n = 0
            solde_n_moins_1 = 0
            #Obtenir liste des comptes details (list des compte lié à un radical)
            for l_account in list_account.get(ref)[3:len(list_account.get(ref))]:
                accounts = False
                list_sauf = []
                if l_account[0] != '_':
                    accounts = self.env["account.account"].search([('code','=like',str(l_account)+'%'),('company_id', '=', self.env.user.company_id.id)])#liste des compte lié a un radical
                    for ac in accounts:#solde des comptes inclus dans chaque radical
                        ac_1=str('_')+ac.code[0:3]
                        ac_2=str('_')+ac.code[0:4]
                        if list_account.get(ref)[0] in ['+', '-'] and ac_1 not in list_account.get(ref)[3:len(list_account.get(ref))] and ac_2 not in list_account.get(ref)[3:len(list_account.get(ref))]:#(solde_n !=0 or solde_n_moins_1 != 0) and
                            solde_n = self.solde_debit_credit([str(ac.code)], date_start_n, date_close_n)[0]
                            solde_n_moins_1 = self.solde_debit_credit([str(ac.code)], date_start_n_moins_1, date_close_n_moins_1)[0]
                            sig_data.append(
                                {'signe': list_account.get(ref)[0], 'ref': ac.code, 'libelle': ac.code +" "+ ac.name,
                                 'groupe': ac.code,
                                 'solde_n': round(abs(solde_n)), 'taux_n': 0.0, 'solde_n_1': round(abs(solde_n_moins_1)),
                                 'taux_n_1': 0.0, 'ecart_n_n1': (round(abs(solde_n)) - round(abs(solde_n_moins_1))),
                                 'taux_ecart_n_n1': 0.0
                                 })
                        if list_account.get(ref)[0] in ['-/+'] and ac_1 not in list_account.get(ref)[3:len(list_account.get(ref))] and ac_2 not in list_account.get(ref)[3:len(list_account.get(ref))]:
                            solde_n = self.solde_debit_credit([str(ac.code)], date_start_n, date_close_n)[0]
                            solde_n_moins_1 = self.solde_debit_credit([str(ac.code)], date_start_n_moins_1, date_close_n_moins_1)[0]
                            sig_data.append(
                                {'signe': self.get_signe_account_line(ref[5:len(ref)], solde_n), 'ref': ac.code,
                                 'libelle': ac.code +" "+ ac.name, 'groupe': ac.code,
                                 'solde_n': round(abs(solde_n)), 'taux_n': 0.0, 'solde_n_1': round(abs(solde_n_moins_1)),
                                 'taux_n_1': 0.0, 'ecart_n_n1': (round(abs(solde_n)) - round(abs(solde_n_moins_1))),
                                 'taux_ecart_n_n1': 0.0
                                 })


        self.sig_report_data = self.list_to_data_json(sig_data)
        sig_data_list = self.sig_report_data_json_to_list()
        # Calcul des lignes globaux
        for sig in sig_data_list:
            if sig.get('ref') == "G_VMP":
                val = self.get_vente_marchandise_production(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})
            if sig.get('ref') == "G_MC":
                val = self.get_marge_commercial(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})
            if sig.get('ref') == "G_PE":
                val = self.get_production_exercice(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})
            if sig.get('ref') == "G_MBP":
                val = self.get_marge_brute_production(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})
            if sig.get('ref') == "G_MBG":
                val = self.get_marge_brute_global(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})
            if sig.get('ref') == "G_VA":
                val = self.get_valeur_ajouter(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})
            if sig.get('ref') == "G_EBE":
                val = self.get_excedent_brut_exploitation(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})
            if sig.get('ref') == "G_REP":
                val = self.get_resultat_exploitation(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})
            if sig.get('ref') == "G_RCO":
                val = self.get_resultat_courant(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})
            if sig.get('ref') == "G_REX":
                val = self.get_resultat_exceptionel(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})
            if sig.get('ref') == "G_RNE":
                val = self.get_resultat_net(sig_data_list)
                sig.update({'solde_n': val.get('som_n'), 'solde_n_1': val.get('som_n_1'),
                            'ecart_n_n1': (val.get('som_n') - val.get('som_n_1'))})

        self.sig_report_data = self.list_to_data_json(sig_data_list)
        # sig_data_list = self.sig_report_data_json_to_list()

        return {}
