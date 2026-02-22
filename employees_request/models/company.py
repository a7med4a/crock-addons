# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"
    print_seal = fields.Binary(string="Print seal")
    print_signature = fields.Binary(string="Print HR Signature")
    admin_signature = fields.Binary(string="Print Admin Signature")
