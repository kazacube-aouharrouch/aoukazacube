# -*- coding: utf-8 -*-
{
    'name': "liasse fiscale de Djibouti",

    'summary': """
        Permet de générer la liasse fiscale de Djibouti """,

    'description': """
        Ce module Permet de générer la liasse fiscale de Djibouti à savoir le Billan, Solde Intermediaire de gestion (SIG)
         Compte de résultat sans oublier d'autres états y afférents.
    """,

    'author': "MYRABILYS TECHNOLOGY sarl",
    'website': "https://web.myrabilys.com",
    'license': 'AGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/tax_return_views.xml',
        'views/account_tax_return_views.xml',
        'report/sig_template_views.xml',
        'report/sig_detail_template_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}