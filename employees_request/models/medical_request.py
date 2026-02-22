# -*- coding: utf-8 -*-آ1ى1

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions


class medical_request(models.Model):
    _name = "emp.medical.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Medical Request"

    medical_authority = fields.Char(string="Medical authority", required=True)
    date_from = fields.Date(string="Date From", required=False)
    date_to = fields.Date(string="Date To", required=False)

    day_number = fields.Integer(
        string="Days Number", required=False, compute="_compute_day_number"
    )

    @api.onchange("date_from", "date_to")
    def _onchange_dates(self):
        for rec in self:
            if rec.date_to and rec.date_from and rec.date_to < rec.date_from:
                raise exceptions.ValidationError(
                    _("Date To Must be grater than Date From")
                )

    @api.depends("date_from", "date_to")
    def _compute_day_number(self):
        for rec in self:
            days = 0
            if rec.date_to and rec.date_from:
                start_date = rec.date_from
                end_date = rec.date_to
                d1 = fields.Datetime.from_string(end_date)
                d2 = fields.Datetime.from_string(start_date)
                delta = d1 - d2
                days = delta.days + 1
            rec.day_number = days

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "confirm"

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("medical.request") or _(
            "New"
        )
        return super(medical_request, self).create(values)

    def action_reprint(self):
        return self.env.ref(
            "employees_request.action_print_employee_medical"
        ).report_action(self)
