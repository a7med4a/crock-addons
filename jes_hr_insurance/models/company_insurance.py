from odoo import api, fields, models


class Insurance_Companies(models.Model):
    _name = "insurance.companies"
    _description = "Insurance Companies Model"

    name = fields.Char(string="Company Name", required=True)
