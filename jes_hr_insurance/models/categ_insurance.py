from odoo import api, fields, models


class Insurance_categ(models.Model):
    _name = "insurance.categ"
    _description = "Insurance Categories"

    name = fields.Char(string="Name", required=True)
