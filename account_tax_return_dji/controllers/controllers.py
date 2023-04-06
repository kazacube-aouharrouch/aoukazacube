# -*- coding: utf-8 -*-
from odoo import http

# class AccountTaxReturnDji(http.Controller):
#     @http.route('/account_tax_return_dji/account_tax_return_dji/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_tax_return_dji/account_tax_return_dji/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_tax_return_dji.listing', {
#             'root': '/account_tax_return_dji/account_tax_return_dji',
#             'objects': http.request.env['account_tax_return_dji.account_tax_return_dji'].search([]),
#         })

#     @http.route('/account_tax_return_dji/account_tax_return_dji/objects/<model("account_tax_return_dji.account_tax_return_dji"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_tax_return_dji.object', {
#             'object': obj
#         })