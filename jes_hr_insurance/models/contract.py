from odoo import api, fields, models
from datetime import datetime

class Contract(models.Model):
    _inherit = "hr.contract"



    medical_insurance_id = fields.Many2one(
        comodel_name="insurance.categ",
        string="Medical Insurance Category",
        store=True, readonly=False
    )

    @api.onchange('grade_id','category_id')
    def onchange_grade(self):
        if self.grade_id.medical_insurance_id:
            self.medical_insurance_id = self.grade_id.medical_insurance_id.id
        elif self.category_id.medical_insurance_id:
            self.medical_insurance_id = self.category_id.medical_insurance_id.id


    @api.onchange('category_id')
    def onchange_category_id(self):
        if self.category_id:
            self.medical_insurance_id = self.category_id.medical_insurance_id


