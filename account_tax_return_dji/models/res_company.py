# -*- coding: utf-8 -*-

'''
Created on 06 Juin. 2019

@author: DESTER
'''
import base64

from odoo import fields, models, api, _

class ResCompany(models.Model):
    """
    Res company add fields
    """

    _inherit = "res.company"

