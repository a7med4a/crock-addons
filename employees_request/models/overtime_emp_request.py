from odoo import models, _, api, fields, models, exceptions
import calendar
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError


class EmpOvertimeRequest(models.Model):
    _name = "emp.overtime.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Overtime Outside Request"

    job_id = fields.Many2one("hr.job", string="Job")
    department_id = fields.Many2one("hr.department", string="Department")

    @api.onchange("overtime_line_ids", "request_date")
    def get_job_department(self):
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    def _getDefaultEmployee(self):
        user_id = self.env.user.id
        employee = (
            self.env["hr.employee"].sudo().search([("user_id", "=", user_id)], limit=1)
        )
        if len(employee) > 0:
            return employee.id
        else:
            return False

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        tracking=True,
        default=_getDefaultEmployee,
    )
    overtime_line_ids = fields.One2many(
        comodel_name="overtime.request.line",
        inverse_name="overtime_request_id",
        string="Overtime Lines",
        required=False,
    )
    job_grade_id = fields.Many2one(
        comodel_name="hr.grade",
        related="employee_id.hr_grade",
        string="Job Grade",
        required=False,
        ondelete="restrict",
    )
    request_date = fields.Date(
        "Request Date", readonly=1, default=lambda self: date.today()
    )
    mission = fields.Char("Mission")

    @api.onchange("overtime_line_ids", "request_date")
    def get_job_department(self):
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    state = fields.Selection(
        string="Status",
        selection=[
            ("draft", "Draft"),
            ("submit", "Submitted"),
            ("approve1", "Manager Approve"),
            ("approve2", "Second Approve"),
            ("audit", "HR Audit"),
            ("reject", "Rejected"),
            ("done", "Done"),
        ],
        default="draft",
        tracking=True,
    )
    pay_batch_created = fields.Boolean("Pay Batch Created", default=False)
    manager_is_user = fields.Boolean(
        string="Manager Is user", compute="check_manager_is_user"
    )
    need_request_id = fields.Many2one("emp.need.request", string="Need Request ")

    @api.onchange("employee_id")
    def onchange_employee_id(self):
        self.overtime_line_ids = False

    @api.depends("employee_id", "employee_id.parent_id")
    def check_manager_is_user(self):
        if self.employee_id.parent_id == self.env.user.employee_id:
            self.manager_is_user = True
        else:
            self.manager_is_user = False

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("overtime.request") or _(
            "New"
        )
        return super(EmpOvertimeRequest, self).create(values)

    def action_submit(self):
        if not self.overtime_line_ids:
            raise UserError(
                _("You Can't Confirm With Empty Lines, Please insert some lines.")
            )
        self.state = "submit"

    def action_approve(self):
        # if self.employee_id.parent_id.id != self.env.user.employee_id.id:
        #     raise UserError(_("You're Not Allowed to Approve. Only manager Can confirm."))
        self.state = "approve1"

    def action_approve2(self):
        self.state = "approve2"

    def action_audit(self):
        # if not self.env.user.has_group('group_audit_employee_deput'):
        #     raise UserError(_("You are not allowed to audit this deputation"))
        self.state = "audit"

    def action_draft(self):
        self.state = "draft"

    def set_to_done(self):
        self.state = "done"
        # self.activity_done()

    def action_reject(self):
        if (
            self.state == "submit"
            and self.employee_id.parent_id.id != self.env.user.employee_id.id
        ):
            raise UserError(_("You are not allowed to reject the request"))

        # elif self.state == 'approve1' and not self.env.user.has_group(
        #         'self_service.second_approve_employee_out_work'):
        #     raise UserError(_("You are not allowed to reject the request"))

        elif self.state in ("approve2", "audit") and not self.env.user.has_group(
            "hr.group_hr_manager"
        ):
            raise UserError(_("You are not allowed to reject the request"))
        self.state = "reject"
        self.activity_done()

    # set all current running activities to done
    def activity_done(self):
        for rec in self.activity_ids:
            rec.action_done()

    # Generate the Pay Over time through Contextual Menu
    def action_generate_pay_overtime(self):
        # The two following conditions to prevent the creation of the batch, if there's an error
        if any(rec.state != "done" for rec in self):
            raise UserError(
                _("You can not generate Pay Overtime To a non-done Overtime")
            )

        if any(rec.pay_batch_created for rec in self):
            raise UserError(
                _("You can not generate Pay Overtime To a Previously Created One")
            )

        pay_travel_obj_batch = self.env["hr.payroll.pay.batch"]
        batch = pay_travel_obj_batch.sudo().create({"type": "pay_overtime"})

        pay_travel_obj = self.env["hr.payroll.pay"]
        for rec in self:
            if not rec.pay_batch_created:
                employee_id = rec.employee_id.id
                pay_type = "pay_overtime"
                number_of_hours = value = 0
                mission = rec.mission
                for line in rec.out_work_line_ids:
                    number_of_days = (line.date_to - line.date_from).days + 1
                    number_of_hours += number_of_days * line.number_of_hours
                    value += line.value

                pay_travel_obj.sudo().create(
                    {
                        "employee_id": employee_id,
                        "value": value,
                        "type": pay_type,
                        "mission": mission,
                        "number_of_hours": number_of_hours,
                        "batch_id": batch.id,
                    }
                )
                rec.pay_batch_created = True


class OvertimeLine(models.Model):
    _name = "overtime.request.line"

    overtime_request_id = fields.Many2one(
        comodel_name="emp.overtime.request", string="OverTime"
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        related="overtime_request_id.employee_id",
        string="Employee",
        store=True,
    )
    state = fields.Selection(
        string="State", related="overtime_request_id.state", store=True
    )
    date_from = fields.Date(string="Date From", required=False)
    date_to = fields.Date(string="Date To", required=False)
    number_of_hours = fields.Float(string="Number Of Hours", required=False)
    total_hours = fields.Float(
        string="Total Hours", required=False, compute="_compute_overtime_hours"
    )
    total_weekdays = fields.Integer(
        string="Normal days", required=False, compute="_compute_overtime_hours"
    )
    weekend_days = fields.Integer(
        string="Weekend Days", required=False, compute="_compute_overtime_hours"
    )
    present_required = fields.Boolean(string="Need Attendance")
    exclude_vacation_days = fields.Boolean(string="Exclude Vacation Days")

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
        "date_from", "date_to", "number_of_hours", "overtime_request_id.employee_id"
    )
    def _compute_overtime_hours(self):
        for rec in self:
            hours = 0.0
            total_weekdays = 0
            weekend_days = 0
            value = 0
            hours_ber_day = rec.number_of_hours or 4
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
                contract = rec.overtime_request_id.employee_id.sudo().contract_id
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

    value = fields.Float("Value", compute="_compute_overtime_hours")
    paid = fields.Boolean("Paid", default=False, readonly=True)
    need_attend = fields.Boolean("Need Attendance", default=False)
    normal_day = fields.Integer("Weekdays")
    days_off = fields.Integer("Weekend days")

    def unlink(self):
        if self.state == "approve2":
            raise ValidationError(_("you cannot delete with 'approved' status ! "))
        return super().unlink()
