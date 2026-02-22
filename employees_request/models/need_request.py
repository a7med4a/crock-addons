# -*- coding: utf-8 -*-آ1ى1

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions
from odoo.exceptions import ValidationError
from datetime import date
import calendar
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError


class NeedOvertimeRequestLine(models.Model):
    _name = "need.overtime.request.line"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    state = fields.Selection(
        [("draft", "To Approve"), ("confirm", "Approved"), ("refuse", "Refused")],
        string="Status",
        readonly=True,
        copy=False,
        default="draft",
    )

    employee_id = fields.Many2one("hr.employee", string="Employee")
    department_id = fields.Many2one("hr.department", string="Department")
    grade_id = fields.Many2one(
        comodel_name="hr.grade",
        related="employee_id.hr_grade",
        string="Job Grade",
        readonly=1,
        store=True,
    )
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    mission = fields.Char("Mission")
    number_of_hours = fields.Float(string="Number Of Hours", required=False)
    total_hours = fields.Float(
        string="Total Hours", required=False, compute="_compute_overtime_hours"
    )
    total_weekdays = fields.Integer(
        string="Normal days", required=False, compute="_compute_overtime_hours"
    )
    weekend_days = fields.Integer(
        string="Vacation Days", required=False, compute="_compute_overtime_hours"
    )
    present_required = fields.Boolean(string="Need Attendance", default=True)
    value = fields.Float("Value", compute="_compute_overtime_hours")
    exclude_vacation_days = fields.Boolean(string="Exclude Vacation Days")
    need_request_id = fields.Many2one("emp.need.request", string="Need Request")

    def count_weekend_days(self, start_date, end_date):
        calendar_id = self.employee_id.contract_id.resource_calendar_id
        weekdays = calendar_id.attendance_ids.filtered(
            lambda line: not line.display_type and line.day_type == "weekend"
        ).mapped("dayofweek")
        weekend_days = 0
        current_date = start_date
        while current_date <= end_date:
            if str(current_date.weekday()) in weekdays:
                weekend_days += 1
            current_date += timedelta(days=1)
        return weekend_days

    @api.depends(
        "employee_id",
        "date_from",
        "date_to",
        "number_of_hours",
        "exclude_vacation_days",
    )
    def _compute_overtime_hours(self):
        for rec in self:
            hours = 0.0
            total_weekdays = 0
            weekend_days = 0
            hours_ber_day = rec.number_of_hours or 4
            value = 0
            if rec.date_from and rec.date_to:
                start_date = datetime.strptime(str(rec.date_from), "%Y-%m-%d")
                end_date = datetime.strptime(str(rec.date_to), "%Y-%m-%d")
                time_difference = end_date - start_date
                total_weekdays = time_difference.days + 1
                weekend_days = rec.count_weekend_days(start_date, end_date)
                if rec.exclude_vacation_days:
                    hours = (total_weekdays - weekend_days) * hours_ber_day
                else:
                    hours = total_weekdays * hours_ber_day
                total_weekdays -= weekend_days
                contract = rec.employee_id.sudo().contract_id
                if contract:
                    basic = contract.get_contract_salary_rule_value(
                        rule_name="wage", date_from=rec.date_from, date_to=rec.date_to
                    )
                    housing = contract.get_contract_salary_rule_value(
                        rule_name="housing",
                        date_from=rec.date_from,
                        date_to=rec.date_to,
                    )
                    trans = contract.get_contract_salary_rule_value(
                        rule_name="transportation",
                        date_from=rec.date_from,
                        date_to=rec.date_to,
                    )
                    total_salary = basic + trans + housing
                    if rec.exclude_vacation_days:
                        normal_value = (total_salary / 160) * total_weekdays
                        vacation_value = 0
                    else:
                        normal_value = (total_salary / 160) * total_weekdays
                        vacation_value = (total_salary / 120) * weekend_days
                    value = (normal_value + vacation_value) * rec.number_of_hours
                else:
                    raise UserError(_("This Employee has no contract"))
            rec.total_hours = hours
            rec.total_weekdays = total_weekdays
            rec.weekend_days = weekend_days
            rec.value = value


class NeedDeputationRequest(models.Model):
    _name = "need.deputation.request.line"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    state = fields.Selection(
        [("draft", "To Approve"), ("confirm", "Approved"), ("refuse", "Refused")],
        string="Status",
        readonly=True,
        copy=False,
        default="draft",
    )

    employee_id = fields.Many2one("hr.employee", string="Employee")
    department_id = fields.Many2one("hr.department", string="Department")
    grade_id = fields.Many2one(
        comodel_name="hr.grade",
        related="employee_id.hr_grade",
        string="Job Grade",
        readonly=1,
        store=True,
    )
    dep_request_type = fields.Selection(
        string="Travel Type",
        required=True,
        selection=[("internal", "Internal"), ("external", "External")],
        default="internal",
    )
    state_id = fields.Many2one("res.country.state", string="City")
    external_id = fields.Many2one("external.actors", string="External Site")
    country_id = fields.Many2one("res.country", string="Country")
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    mission = fields.Char("Mission")
    cost_with_allowances = fields.Float(
        "Cost With (house-food-transportation)", compute="compute_total_allowance"
    )
    cost_without_allowances = fields.Float(
        "Cost Without (house-food-transportation)", compute="compute_total_allowance"
    )
    description = fields.Text("Description")
    need_request_id = fields.Many2one("emp.need.request", string="Need Request")
    number_of_days = fields.Integer(
        string="Number Of Days", required=False, compute="compute_total_allowance"
    )
    cost_days = fields.Integer(
        string="Cost depend on Days", required=False, compute="compute_total_allowance"
    )

    @api.depends(
        "employee_id",
        "grade_id",
        "country_id",
        "dep_request_type",
        "date_from",
        "date_to",
    )
    def compute_total_allowance(self):
        for rec in self:
            trans = (rec.employee_id.hr_grade.transport) / 30
            if rec.date_from and rec.date_to:
                number_of_days = cost_days = (rec.date_to - rec.date_from).days + 1
                if rec.dep_request_type == "internal":
                    amount = rec.sudo().grade_id.internal_secondment
                    cost_days += 2
                else:
                    cost_days += rec.country_id.days_after + rec.country_id.days_before
                    if not rec.country_id or not rec.country_id.country_degree:
                        amount = 0
                    else:
                        if rec.country_id.country_degree == "first":
                            amount = rec.sudo().grade_id.outside_a_secondment
                        elif rec.country_id.country_degree == "second":
                            amount = rec.sudo().grade_id.outside_b_secondment
                        elif rec.country_id.country_degree == "third":
                            amount = rec.sudo().grade_id.outside_c_secondment
                        else:
                            amount = rec.sudo().grade_id.outside_hard_secondment
            else:
                amount = 0
                number_of_days = cost_days = 0
            rec.number_of_days = number_of_days
            rec.cost_days = cost_days
            trans_amount = trans * cost_days
            cost_with_allowances = (amount * 0.25 * cost_days) - trans_amount
            cost_without_allowances = (amount * cost_days) + trans_amount
            if cost_with_allowances > 0:
                rec.cost_with_allowances = cost_with_allowances
            else:
                rec.cost_with_allowances = 0
            if cost_without_allowances > 0:
                rec.cost_without_allowances = cost_without_allowances
            else:
                rec.cost_without_allowances = 0


class FieldWorkLines(models.Model):
    _name = "field.work.lines"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    state = fields.Selection(
        [("draft", "To Approve"), ("confirm", "Approved"), ("refuse", "Refused")],
        string="Status",
        readonly=True,
        copy=False,
        default="draft",
    )

    employee_id = fields.Many2one("hr.employee", string="Employee")
    department_id = fields.Many2one("hr.department", string="Department")
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    mission = fields.Char("Mission")
    need_request_id = fields.Many2one("emp.need.request", string="Need Request")

    def action_approve_field_work(self):
        for record in self:
            record.state = "confirm"

    def action_refuse_field_work(self):
        for record in self:
            record.state = "refuse"

    @api.onchange("department_id")
    def get_employee_domain(self):
        for record in self:
            all_employees = []
            employee_obj = self.env["hr.employee"].sudo().search([])
            for emp in employee_obj:
                if record.department_id.id == emp.department_id.id:
                    all_employees.append(emp.id)
            return {"domain": {"employee_id": [("id", "in", all_employees)]}}


class EmpNeedRequest(models.Model):
    _name = "emp.need.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Need Request"

    need_type = fields.Selection(
        [
            ("deputation", "Deputation"),
            ("assigned", "Assigned"),
            ("field_work", "Field work"),
        ],
        string="Type",
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=False,
        default=lambda self: self.env.user.employee_id,
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
    # request_type = fields.Selection(
    #     [('inside', 'Inside the kingdom'), ('outside', 'Outside the kingdom')],
    #     string='Request Type',
    #     states={'cancel': [('readonly', True)], 'confirm': [('readonly', True)], 'refuse': [('readonly', True)],
    #             'validate': [('readonly', True)], 'validate2': [('readonly', True)]},
    #     )
    # country_id = fields.Many2one('res.country', string='Country',
    #                              states={'cancel': [('readonly', True)], 'confirm': [('readonly', True)],
    #                                      'refuse': [('readonly', True)],
    #                                      'validate': [('readonly', True)], 'validate2': [('readonly', True)]})
    # state_id = fields.Many2one('res.country.state', string='State',
    #                            states={'cancel': [('readonly', True)], 'confirm': [('readonly', True)],
    #                                    'refuse': [('readonly', True)],
    #                                    'validate': [('readonly', True)], 'validate2': [('readonly', True)]})
    city_id = fields.Many2one(
        "res.city",
        "City",
        states={
            "cancel": [("readonly", True)],
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "validate": [("readonly", True)],
            "validate2": [("readonly", True)],
        },
    )
    reason = fields.Text(
        "Reason",
        states={
            "cancel": [("readonly", True)],
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "validate": [("readonly", True)],
            "validate2": [("readonly", True)],
        },
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
    )

    journal_id = fields.Many2one(
        "account.journal",
        domain="[('type', 'in', ('bank', 'cash'))]",
        states={
            "cancel": [("readonly", True)],
            "confirm": [("readonly", False)],
            "refuse": [("readonly", True)],
            "validate2": [("readonly", True)],
        },
    )

    hide_field = fields.Boolean(compute="_compute_visible")

    # /////////////////////
    field_work = fields.One2many(
        "field.work.lines", "need_request_id", string="Field Work"
    )
    deputation_request_line_ids = fields.One2many(
        "need.deputation.request.line",
        "need_request_id",
        string="Deputation Request Line",
    )
    overtime_request_line_ids = fields.One2many(
        "need.overtime.request.line", "need_request_id", string="Overtime Request Line"
    )

    def action_create_overtime(self):
        for record in self:
            request_ids = []
            for line in record.overtime_request_line_ids:
                line_ids = []
                overtime_dict = {
                    "employee_id": line.employee_id.id,
                    "request_date": record.request_date,
                    # 'grade_id': record.grade_id.id,
                    "mission": line.mission,
                    # 'description': record.description,
                    "need_request_id": record.id,
                }
                overtime_lines = (
                    0,
                    0,
                    {
                        "date_from": line.date_from,
                        "date_to": line.date_to,
                        "number_of_hours": line.number_of_hours,
                        "total_hours": line.total_hours,
                        "total_weekdays": line.total_weekdays,
                        "weekend_days": line.weekend_days,
                        "present_required": line.present_required,
                        "exclude_vacation_days": line.exclude_vacation_days,
                        "value": line.value,
                    },
                )
                line_ids.append(overtime_lines)
                overtime_dict["overtime_line_ids"] = line_ids
                request_ids.append(overtime_dict)
            self.env["emp.overtime.request"].create(request_ids)

    def open_deputation(self):
        return {
            "name": _("Deputation"),
            "type": "ir.actions.act_window",
            "view_type": "tree",
            "view_mode": "tree,form",
            "res_model": "emp.deputation.request",
            "context": {"create": True, "edit": True},
            "target": "current",
            "domain": [("request_need_id", "=", self.id)],
        }

    def open_overtime(self):
        return {
            "name": _("Overtime"),
            "type": "ir.actions.act_window",
            "view_type": "tree",
            "view_mode": "tree,form",
            "res_model": "emp.overtime.request",
            "context": {"create": True, "edit": True},
            "target": "current",
            "domain": [("need_request_id", "=", self.id)],
        }

    def _compute_deputation_count(self):
        self.deputation_count = self.env["emp.deputation.request"].search_count(
            [("request_need_id", "=", self.id)]
        )

    deputation_count = fields.Integer(
        "Deputation Count", compute="_compute_deputation_count"
    )

    def _compute_overtime_count(self):
        self.overtime_count = self.env["emp.overtime.request"].search_count(
            [("need_request_id", "=", self.id)]
        )

    overtime_count = fields.Integer("Overtime Count", compute="_compute_overtime_count")

    def action_create_deputation(self):
        for record in self:
            request_ids = []
            for line in record.deputation_request_line_ids:
                line_ids = []
                deputation_dict = {
                    "employee_id": line.employee_id.id,
                    "request_date": record.request_date,
                    "grade_id": line.grade_id.id,
                    "mission": line.mission,
                    "description": line.description,
                    "request_need_id": record.id,
                }
                deputation_lines = (
                    0,
                    0,
                    {
                        "request_type": line.dep_request_type,
                        "external_id": line.external_id.id,
                        "state_id": line.state_id.id,
                        "country_id": line.country_id.id,
                        "date_from": line.date_from,
                        "date_to": line.date_to,
                    },
                )
                line_ids.append(deputation_lines)
                deputation_dict["deputation_line_ids"] = line_ids
                request_ids.append(deputation_dict)
            self.env["emp.deputation.request"].create(request_ids)

    @api.depends("employee_id")
    def _compute_visible(self):
        for rec in self:
            if self.env.user.has_group("hr.group_hr_user") or self.env.user.has_group(
                "account.group_account_manager"
            ):
                rec.hide_field = False
            else:
                rec.hide_field = True

    job_id = fields.Many2one("hr.job", string="Job")
    department_id = fields.Many2one("hr.department", string="Department")

    @api.onchange("request_date", "employee_id")
    def onchange_request_date(self):
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    @api.constrains("cost")
    def _check_amount(self):
        for rec in self:
            if rec.cost <= 0 and rec.state != "draft":
                raise ValidationError(_("Cost Can Not Be 0 or Less"))

    def action_confirm(self):
        self.write({"state": "confirm"})
        return True

    def action_refuse(self):
        self.write({"state": "refuse"})
        # self.activity_done()
        return True

    def action_Approved(self):
        self.write({"state": "validate"})
        # self.activity_done()
        # # Sending Notification TO Accountant administrators
        # for user in self.env['res.users'].search([]):
        #     if user.has_group('account.group_account_manager'):
        #         self.activity_schedule(
        #             activity_type_id=self.env.ref('mail_act_request_need').id,
        #             summary=_('New Request Need Needs Approve'), user_id=user.id)

        return True

    # def action_approve2(self):
    #     pay_account = int(self.env['ir.config_parameter'].sudo().get_param('request_need_debit_account_id')) or 0
    #     move_dict = {
    #         'journal_id': self.journal_id.id,
    #         'date': date.today(),
    #         'ref': "Request Need"
    #     }
    #     line_ids = []
    #     debit_vals = {
    #         'name': "Request Need",
    #         'partner_id': self.employee_id.user_partner_id.id,
    #         'account_id': pay_account,
    #         'debit': self.cost,
    #         'credit': 0
    #     }
    #     line_ids.append(debit_vals)
    #
    #     credit_vals = {
    #         'name': "Request Need",
    #         'partner_id': self.employee_id.user_partner_id.id,
    #         'account_id': self.journal_id.default_account_id.id,
    #         'debit': 0,
    #         'credit': self.cost
    #     }
    #
    #     line_ids.append(credit_vals)
    #
    #     move_dict['line_ids'] = [(0, 0, line) for line in line_ids]
    #     self.env['account.move'].create(move_dict)
    #     self.write({'state': 'validate2'})
    #     # self.activity_done()
    #
    #     return True

    # set all current running activities to done

    def activity_done(self):
        for rec in self.activity_ids:
            rec.action_done()

    def unlink(self):
        if self.filtered(lambda x: x.state == "validate"):
            raise ValidationError(_("you cannot delete with 'approved' status ! "))
        return super(EmpNeedRequest, self).unlink()

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("need.request") or _(
            "New"
        )
        return super(EmpNeedRequest, self).create(values)
