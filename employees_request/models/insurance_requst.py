from odoo import models, _, api, fields, models, exceptions
import calendar
from datetime import datetime


class insurance_relation(models.Model):
    _name = "insurance.relation"
    _rec_name = "name"
    _description = "New Description"

    name = fields.Char()


class emp_insurance_request(models.Model):
    _name = "emp.insurance.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Insurance Request"

    family_line_ids = fields.One2many(
        comodel_name="insurance.request.line",
        inverse_name="insurance_request_id",
        string="Family Member",
        required=False,
    )
    job_id = fields.Many2one("hr.job", string="Job")
    department_id = fields.Many2one("hr.department", string="Department")

    @api.onchange("employee_id", "description", "family_line_ids")
    def onchange_request_date(self):
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(emp_insurance_request, self).unlink()

    def action_confirm_insh(self):
        self.state = "confirm"
        for line in self.family_line_ids:
            line.parent_employee_id = self.employee_id.id

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("insurance.request") or _(
            "New"
        )
        return super(emp_insurance_request, self).create(values)


class insuranceline(models.Model):
    _name = "insurance.request.line"

    fm_name_ar = fields.Char(string="Name AR.", required=True)
    fm_name_en = fields.Char(string="Name EN.", required=True)
    insurance_request_id = fields.Many2one(
        comodel_name="emp.insurance.request", string="Insurance"
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        related="insurance_request_id.employee_id",
        string="Employee",
    )
    parent_employee_id = fields.Many2one(
        comodel_name="hr.employee", string="Parent Employee"
    )
    identification_id = fields.Char(string="Identification", required=False)
    relation_id = fields.Many2one(
        comodel_name="insurance.relation", string="Relation Type", required=True
    )
    has_insurance = fields.Boolean("Has Insurance")
    birthdate = fields.Date(string="Birthdate", required=True)
    gender_type = fields.Selection(
        string="Type",
        selection=[("male", "Male"), ("female", "Female")],
        required=True,
        tracking=True,
    )
    # fm_passport_id = fields.Char(string="Family Member Passport", required=False, )
    add_date = fields.Date(
        string="Add Date",
        required=True,
        default=fields.datetime.now(),
        states={"draft": [("readonly", False)]},
    )
    fm_phone = fields.Char(string="Phone", required=False)

    related_attach = fields.Many2many(
        "ir.attachment", string="Related attachment", ondelete="cascade", required=True
    )
    related_attachment = fields.Binary(string="Related attachment", required=True)
    attachment_name = fields.Char()

    # @api.model
    # def create(self, values):
    #     rec = super(insuranceline, self).create(values)
    #
    #     if not rec.related_attach:
    #
    #         raise exceptions.ValidationError(_('Attachment Is Required'))
    #     return rec
    #
