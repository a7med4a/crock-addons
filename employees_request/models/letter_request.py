# -*- coding: utf-8 -*-آ1ى1

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions


class letter_request(models.Model):
    _name = "letter.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Identification Letters Request"

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(letter_request, self).unlink()

    name = fields.Char(string="letter")
    destination = fields.Char(string="To Whom", required=True)
    note = fields.Text(string="Note", required=False)
    letter_type = fields.Selection(
        string="Salary Identification",
        selection=[
            ("with_salary", "With Salary"),
            ("without_salary", "Without salary"),
        ],
        default="with_salary",
        required=False,
        tracking=True,
    )

    company_id = fields.Many2one(
        "res.company", readonly=True, default=lambda self: self.env.company
    )

    no_copy = fields.Integer(string="No. Copy", required=False, default=1)

    job_id = fields.Many2one("hr.job", string="Job")
    department_id = fields.Many2one("hr.department", string="Department")

    @api.onchange("destination", "employee_id")
    def onchange_request_date(self):
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "confirm"
                return self.env.ref(
                    "employees_request.action_print_employee_letter"
                ).report_action(self)

    def action_reprint(self):
        return self.env.ref(
            "employees_request.action_print_employee_letter"
        ).report_action(self)

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("letter.request") or _(
            "New"
        )
        return super(letter_request, self).create(values)
