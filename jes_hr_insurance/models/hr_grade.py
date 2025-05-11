from odoo import models, fields, api

class GradeCategory(models.Model):
    _inherit = "grade.category"

    medical_insurance_id = fields.Many2one(
        "insurance.categ", string="Medical Insurance Category"
    )
    def update_medical(self):
        if self.medical_insurance_id:
            all_grades = self.env['hr.salary.grade'].sudo().search([('category_id','=',self.id)])
            all_grades.write({'medical_insurance_id':self.medical_insurance_id.id})
            all_contract = self.env['hr.contract'].sudo().search([('grade_id', 'in', all_grades.ids)])
            all_contract.write({'medical_insurance_id': self.medical_insurance_id.id})


class HrSalaryGrade(models.Model):
    _inherit = "hr.salary.grade"


    medical_insurance_id = fields.Many2one(
        comodel_name="insurance.categ",
        string="Medical Insurance Category",
        store=True, readonly=False
    )

    @api.onchange('category_id')
    def onchange_category_id(self):
        if self.category_id:
            self.medical_insurance_id = self.category_id.medical_insurance_id
