# -*- coding: utf-8 -*-
# Copyright 2021 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError, Warning, AccessError
from odoo.tools import float_is_zero, float_compare
from itertools import groupby
from . import calverter

import json
from . import calverter


class HrAppraisal(models.Model):
    _inherit = "hr.appraisal"
    appraisal_level = fields.Selection(
        selection=[
            ("50-60", "First-Level"),
            ("61-62", "Second-Level"),
            ("63-64", "Third-Level"),
            ("70-72", "Expert"),
        ],
        string="Appraisal Level",
        default="50-60",
        tracking=True,
        required=True,
    )


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def get_islamic_date(self, date):
        date = str(date)
        date_list = str(date).split("-")
        cal = calverter.Calverter()
        jd = cal.gregorian_to_jd(
            int(date_list[0]), int(date_list[1]), int(date_list[2])
        )
        islamic_date = cal.jd_to_islamic(jd)
        islamic_date_format = (
            str(islamic_date[0])
            + "-"
            + str(islamic_date[1])
            + "-"
            + str(islamic_date[2])
        )
        return islamic_date_format

    balance_leave_days = fields.Integer(string="Balance Leave Days")
    travel_ticket_value = fields.Float(string="Travel Ticket Value")
    loan_status = fields.Selection(
        string="Loan status", selection=[("yes", "Yes"), ("no", "No")]
    )
    date_last_bouns_hous = fields.Date(
        string="Date Last Housing Allowance", required=False
    )
    return_date_lst_lev = fields.Date(
        string="Return Date of Last Leave", required=False
    )
    balance = fields.Float(string="Balance", required=False, compute="compute_balance")
    job_num = fields.Char(string="Job Number", required=False)

    family_line_ids = fields.One2many(
        comodel_name="insurance.request.line",
        inverse_name="employee_id",
        string="Family",
        required=False,
    )

    insurance_count = fields.Integer(
        string="Insurance Count", required=False, compute="compute_insurance_count"
    )
    study_field_id = fields.Many2one(
        comodel_name="study.field", string="Study Field", required=False
    )
    study_date = fields.Date(string="Study Date", required=False)

    def compute_insurance_count(self):
        for rec in self:
            insh_ids = self.env["emp.insurance.request"].search_count(
                [("employee_id", "=", rec.id)]
            )
            rec.insurance_count = insh_ids

    def action_open_insurance(self):
        insh_ids = self.env["emp.insurance.request"].search(
            [("employee_id", "=", self.id)]
        )
        return {
            "name": _("Insurance"),
            "type": "ir.actions.act_window",
            "view_type": "tree",
            "view_mode": "tree,form",
            "res_model": "emp.insurance.request",
            "context": {"create": True, "edit": True},
            "target": "current",
            "domain": [("id", "in", insh_ids.ids)],
        }

    @api.depends("address_home_id")
    def compute_balance(self):
        for rec in self:
            credit = 0.0
            debit = 0.0
            if rec.address_home_id:
                moves = (
                    self.env["account.move.line"]
                    .sudo()
                    .search(
                        [
                            ("move_id.state", "=", "posted"),
                            ("partner_id", "=", rec.address_home_id.id),
                        ]
                    )
                )
                credit = sum(moves.mapped("credit"))
                debit = sum(moves.mapped("debit"))
            rec.balance = debit - credit


class hr_salary_rule(models.Model):
    _inherit = "hr.salary.rule"

    due_salary = fields.Boolean(string="Due Salary")
