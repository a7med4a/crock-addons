from odoo import api, fields, models


class Insurance_pricing(models.Model):
    _name = "insurance.pricing"
    _rec_name = "company_id"
    _description = "Insurance Pricing"

    company_id = fields.Many2one(
        comodel_name="insurance.companies", string="Insurance Company", required=True
    )
    insurance_categ_id = fields.Many2one(
        comodel_name="insurance.categ", string="Insurance Category", required=True
    )
    male_categ_cost = fields.Float(string="Male Category Cost", required=True)
    female_categ_cost = fields.Float(string="Female Category Cost", required=True)
    male_cost = fields.Float(string="Male Cost", required=True)
    female_cost = fields.Float(string="Female Cost", required=True)
    father_cost = fields.Float(string="Father Cost", required=True)
    mother_cost = fields.Float(string="Mother Cost", required=True)
