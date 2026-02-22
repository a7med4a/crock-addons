# -*- coding: utf-8 -*-آ1ى1

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    has_salary_breakdown = fields.Boolean(string="Has Salary Breakdown")


class salary_breakdown_request(models.Model):
    _name = "emp.salary_breakdown.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Salar BreakDown Request"

    #
    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(salary_breakdown_request, self).unlink()

    iban_number = fields.Char(
        string="Currant IBAN Number",
        related="employee_id.iban_number",
        required=False,
        store=True,
    )
    bank_id = fields.Many2one(
        comodel_name="res.bank",
        related="employee_id.bank_id",
        string="Bank Name",
        store=True,
        required=False,
    )
    new_iban_number = fields.Char(string="Currant IBAN Number", required=False)

    new_bank_id = fields.Many2one(
        comodel_name="res.bank", string="New Bank Name", required=False
    )

    related_attach = fields.Many2many(
        "ir.attachment", string="Attachment", ondelete="cascade"
    )
    related_attachment = fields.Binary(string="Attachment", required=True)
    attachment_name = fields.Char()

    def action_confirm(self):
        for rec in self:
            rec.check_breakdown()
            if rec.state == "draft":
                rec.state = "confirm"

    def check_breakdown(self):
        for rec in self:
            if rec.employee_id.has_salary_breakdown:
                raise exceptions.ValidationError(
                    _("This employee has a Salary Breakdown")
                )
            else:

                rec.employee_id.has_salary_breakdown = True
                rec.employee_id.bank_id = rec.new_bank_id
                rec.employee_id.iban_number = rec.iban_number

    def action_aprro(self):
        for rec in self:
            rec.state = "Approved"

    def action_reprint(self):
        return self.env.ref(
            "employees_request.action_print_employee_salary_breakdown"
        ).report_action(self)

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("breakdown.request") or _(
            "New"
        )
        return super(salary_breakdown_request, self).create(values)
