# -*- coding: utf-8 -*-آ1ى1

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions
from odoo.exceptions import ValidationError
from datetime import date


class ticket_request(models.Model):
    _name = "emp.ticket.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Ticket Request"

    employee_id = fields.Many2one(
        "hr.employee",
        default=lambda self: self.env.user.employee_id,
        string="Employee",
        states={
            "cancel": [("readonly", True)],
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "validate": [("readonly", True)],
            "validate2": [("readonly", True)],
        },
        required=True,
    )
    request_date = fields.Date(
        "Request Date",
        readonly=True,
        states={
            "cancel": [("readonly", True)],
            "refuse": [("readonly", True)],
            "confirm": [("readonly", True)],
            "validate": [("readonly", True)],
            "validate2": [("readonly", True)],
        },
        tracking=True,
        required=True,
        default=lambda self: date.today(),
    )
    state = fields.Selection(
        [
            ("draft", "To Submit"),
            ("confirm", "To Approve"),
            ("refuse", "Refused"),
            ("validate", "Approved"),
            ("validate2", "Accounting Approved"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        default="draft",
    )

    job_id = fields.Many2one("hr.job", string="Job")
    department_id = fields.Many2one("hr.department", string="Department")
    request_type = fields.Selection(
        [("normal_vacation", "Normal Vacation"), ("termination", "Termination")],
        string="Request Type",
        states={
            "cancel": [("readonly", True)],
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "validate": [("readonly", True)],
            "validate2": [("readonly", True)],
        },
        required=True,
    )
    cost = fields.Float(
        "Cost",
        states={
            "cancel": [("readonly", True)],
            "confirm": [("readonly", False)],
            "refuse": [("readonly", True)],
            "validate": [("readonly", True)],
            "validate2": [("readonly", True)],
        },
        required=False,
    )

    journal_id = fields.Many2one(
        "account.journal",
        domain="[('type', 'in', ('bank', 'cash'))]",
        states={
            "cancel": [("readonly", True)],
            "confirm": [("readonly", False)],
            "refuse": [("readonly", True)],
            "validate": [("readonly", True)],
            "validate2": [("readonly", True)],
        },
        required=False,
    )
    ticket_type = fields.Selection(
        string="Ticket",
        selection=[("Leave", "Leave"), ("End-Service", "End-Service")],
        required=True,
    )
    date_from = fields.Date(string="Date From", required=False)
    date_to = fields.Date(string="Date To", required=False)
    day_number = fields.Integer(string="Days Number", required=False)

    job_id = fields.Many2one("hr.job", string="Job")
    department_id = fields.Many2one("hr.department", string="Department")

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

    @api.onchange("request_date", "employee_id")
    def onchange_request_date(self):
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    hide_field = fields.Boolean(compute="_compute_visible")

    @api.onchange("request_date", "employee_id")
    def onchange_request_date(self):
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    @api.depends("employee_id")
    def _compute_visible(self):
        for rec in self:
            if self.env.user.has_group("hr.group_hr_user") or self.env.user.has_group(
                "account.group_account_manager"
            ):
                rec.hide_field = False
            else:
                rec.hide_field = True

    def action_confirm(self):
        self.write({"state": "confirm"})
        return True

    def action_refuse(self):
        self.write({"state": "refuse"})
        return True

    def action_approve(self):
        self.write({"state": "validate"})
        return True

    def action_approve2(self):
        pay_account = (
            int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("ticket_request_debit_account_id")
            )
            or 0
        )
        move_dict = {
            "journal_id": self.journal_id.id,
            "date": fields.Date.today(),
            "ref": "pay_type",
        }
        line_ids = []
        debit_vals = {
            "name": "Ticket Request",
            "partner_id": self.employee_id.user_partner_id.id,
            "account_id": pay_account,
            "debit": self.cost,
            "credit": 0,
        }
        line_ids.append(debit_vals)
        credit_vals = {
            "name": "Ticket Request",
            "partner_id": self.employee_id.user_partner_id.id,
            "account_id": self.journal_id.default_account_id.id,
            "debit": 0,
            "credit": self.cost,
        }
        line_ids.append(credit_vals)
        move_dict["line_ids"] = [(0, 0, line) for line in line_ids]
        self.env["account.move"].create(move_dict)
        self.write({"state": "validate2"})
        return True

    def activity_done(self):
        for rec in self.activity_ids:
            rec.action_done()

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("ticket.request") or _(
            "New"
        )
        return super(ticket_request, self).create(values)
