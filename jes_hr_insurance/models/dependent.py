from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime



class Dependent(models.Model):
    _inherit = "hr.family"
    _description = "Dependent Data"

    addition_date = fields.Date(
        string="Addition Date", required=True, default=fields.Date.context_today
    )
    insurance_add_id = fields.Many2one(
        comodel_name="insurance.add.delete", string="Add or Delete insurance"
    )
    has_insurance = fields.Boolean("Has Insurance")
    last_add_insurance = fields.Date("Last Add Insurance Date")
    last_delete_insurance = fields.Date("Last Delete Insurance Date")
    insurance_cost = fields.Float(string="Insurance Cost", required=False)




