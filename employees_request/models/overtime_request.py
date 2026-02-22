# -*- coding: utf-8 -*-آ1ى1

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions
import calendar
from datetime import datetime


class OvertimeRequest(models.Model):
    _name = "overtime.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "OverTime Request"

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(OvertimeRequest, self).unlink()

    name = fields.Char(string="Request", readonly=True)
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        required=True,
        string="Employee",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env.user.employee_id,
    )
    request_date = fields.Date(
        string="Request Date",
        required=True,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=fields.Date.context_today,
    )
    policy_id = fields.Many2one(
        comodel_name="overtime.policy", string="Overtime Policy", required=False
    )
    contract_id = fields.Many2one(
        comodel_name="hr.contract",
        string="Contract",
        related="employee_id.contract_id",
        required=True,
        tracking=True,
    )
    contract_start_date = fields.Date(
        string="Contract Start Date",
        related="contract_id.first_contract_date",
        tracking=True,
    )
    total_hours = fields.Float(
        string="Total Hours",
        compute="_compute_total_hours",
        compute_sudo=True,
        store=True,
    )
    total_request_amount = fields.Float(
        string="Total Overtime Amount",
        compute="_compute_total_hours",
        compute_sudo=True,
        store=True,
    )
    salary_amount = fields.Float(
        string="Salary Amount",
        compute="_compute_total_hours",
        compute_sudo=True,
        store=True,
    )
    state = fields.Selection(
        string="State",
        selection=[("draft", "Draft"), ("confirm", "Confirm"), ("paid", "Paid")],
        default="draft",
        required=False,
    )

    normal_hour_rate = fields.Float(string="Normal Hour Rate", required=False)
    max_normal_hour = fields.Float(string="Max Normal Hour", required=False)
    normal_hour = fields.Float(string="Normal Hour", required=False)
    public_hour_rate = fields.Float(string="Public Hour Rate", required=False)
    max_public_hour = fields.Float(string="Max Public Hour", required=False)
    public_hour = fields.Float(string="Public Hour", required=False)
    weekend_hour_rate = fields.Float(string="Weekend Hour Rate", required=False)
    max_weekend_hour = fields.Float(string="Max Weekend Hour", required=False)
    weekend_hour = fields.Float(string="Weekend Hour", required=False)

    emp_readonly = fields.Boolean(
        string="Make employee Readonly", compute="_compute_field_readonly", store=True
    )

    # @api.depends("employee_id")
    # def _compute_field_readonly(self):
    #     for record in self:
    #         ss_group = self.env.user.has_group(
    #             "employees_request.group_self_services_request"
    #         )
    #         admin_group = self.env.user.has_group(
    #             "employees_request.emp_request_access_group_admin"
    #         )
    #         if ss_group and not admin_group:
    #             record.emp_readonly = True
    #         else:
    #             record.emp_readonly = True
    @api.depends("employee_id")
    def _compute_field_readonly(self):
        for record in self:
            ss_group = self.env.user.has_group(
                "employees_request.group_self_services_request"
            )
            admin_group = self.env.user.has_group(
                "employees_request.emp_request_access_group_admin"
            )
            if self.env.user.has_group(
                "employees_request.emp_request_access_group_admin"
            ):
                self.emp_readonly = 0
            else:
                self.emp_readonly = 1

    @api.onchange("policy_id")
    def onchange_overtime_policy_id(self):
        self.normal_hour_rate = self.policy_id.normal_hour_rate
        self.max_normal_hour = self.policy_id.max_normal_hour
        self.public_hour_rate = self.policy_id.public_hour_rate
        self.max_public_hour = self.policy_id.max_public_hour
        self.weekend_hour_rate = self.policy_id.weekend_hour_rate
        self.max_weekend_hour = self.policy_id.max_weekend_hour

    @api.depends(
        "normal_hour",
        "public_hour",
        "weekend_hour",
        "normal_hour_rate",
        "public_hour_rate",
        "weekend_hour_rate",
        "max_normal_hour",
        "max_public_hour",
        "max_weekend_hour",
    )
    def _compute_total_hours(self):
        for rec in self:
            total_hours = 0
            if rec.normal_hour:
                normal_hour = (
                    rec.normal_hour
                    if rec.normal_hour <= rec.max_normal_hour
                    else rec.max_normal_hour
                )
                total_hours += normal_hour * rec.normal_hour_rate
            if rec.public_hour:
                public_hour = (
                    rec.public_hour
                    if rec.public_hour <= rec.max_public_hour
                    else rec.max_public_hour
                )
                total_hours += public_hour * rec.public_hour_rate
            if rec.weekend_hour:
                weekend_hour = (
                    rec.weekend_hour
                    if rec.weekend_hour <= rec.max_weekend_hour
                    else rec.max_weekend_hour
                )
                total_hours += weekend_hour * rec.weekend_hour_rate
            rec.total_hours = total_hours
            request_date = (
                fields.Date.to_date(rec.request_date) or datetime.now().today()
            )
            year = request_date.year
            month = request_date.month
            month_days = calendar.monthrange(year, month)[1]
            salary_amount = rec.contract_id.wage
            if rec.policy_id.calc_type == "basic_allowance":
                non_calc_alw = 0.0
                calc_alw = 0.0
                non_calc_alw_names = []
                for field in rec.policy_id.non_calc_allowance_ids:
                    non_calc_alw += rec.contract_id[field.name]
                    non_calc_alw_names.append(field.name)
                if "housing" not in non_calc_alw_names:
                    calc_alw += rec.contract_id["housing"]
                if "other_allowance" not in non_calc_alw_names:
                    calc_alw += rec.contract_id["other_allowance"]
                if "transportation" not in non_calc_alw_names:
                    calc_alw += rec.contract_id["transportation"]
                salary_amount += calc_alw
            hours_per_day = rec.employee_id.resource_calendar_id.hours_per_day or 8
            hour_amount = salary_amount / month_days / hours_per_day
            total_request_amount = total_hours * hour_amount
            rec.total_request_amount = total_request_amount
            rec.salary_amount = salary_amount

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                # rec.confirm_entry()
                rec.state = "confirm"

    def action_paid(self):
        for rec in self:
            if rec.state == "confirm":
                # rec.pay_entry()
                rec.state = "paid"

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("overtime.order") or _(
            "New"
        )
        return super(OvertimeRequest, self).create(values)
