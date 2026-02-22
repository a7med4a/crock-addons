from odoo import models, _, api, fields, models, exceptions
import calendar
from datetime import datetime, date
from odoo.exceptions import UserError
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError


class Country(models.Model):
    _inherit = "res.country"

    ar_name = fields.Char(string="Arabic Name", required=False)
    days_after = fields.Integer("Number of Days after", default=0)
    days_before = fields.Integer("Number of Days before", default=0)


class CountryGroup(models.Model):
    _inherit = "res.country.group"

    ar_name = fields.Char(
        string="Arabic Name",
        required=False,
    )
    country_degree = fields.Selection(
        [
            ("first", "First"),
            ("second", "Second"),
            ("third", "Third"),
            ("hard", "Hard"),
        ],
        string="Country degree",
    )
    days_after = fields.Integer("Number of Days after", default=0)
    days_before = fields.Integer("Number of Days before", default=0)

    def update_country_degree(self):
        for group in self:
            for country in group.country_ids:
                country.days_after = group.days_after
                country.days_before = group.days_before
                country.country_degree = group.country_degree


class EmployeeDeputation(models.Model):
    _name = "emp.deputation.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Deputation Request"

    deputation_line_ids = fields.One2many(
        comodel_name="deputation.request.line",
        inverse_name="deputation_request_id",
        string="Deputation Lines",
        required=False,
        tracking=True,
        readonly=1,
        states={"draft": [("readonly", False)]},
    )
    mission = fields.Char(string="mission", required=False)
    job_id = fields.Many2one("hr.job", string="Job")
    department_id = fields.Many2one("hr.department", string="Department")

    @api.onchange("request_date", "employee_id")
    def onchange_request_date(self):
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    grade_id = fields.Many2one(
        comodel_name="hr.grade",
        related="employee_id.hr_grade",
        string="Job Grade",
        readonly=1,
        store=True,
    )

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
        readonly=1,
        states={"draft": [("readonly", False)]},
        default=_getDefaultEmployee,
    )
    request_date = fields.Date(
        "Request Date", readonly=1, default=lambda self: date.today()
    )
    note = fields.Char("Note")
    pay_batch_created = fields.Boolean(default=False)

    state = fields.Selection(
        string="Status",
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("approve1", "Manager Approve"),
            ("approve2", "Second Approve"),
            ("audit", "HR Audit"),
            ("reject", "Rejected"),
            ("done", "Done"),
        ],
        default="draft",
        tracking=True,
    )
    manager_is_user = fields.Boolean(
        string="Manager Is user", compute="check_manager_is_user"
    )
    request_need_id = fields.Many2one("emp.need.request", string="Need Request")

    @api.depends("employee_id", "employee_id.parent_id")
    def check_manager_is_user(self):
        if self.employee_id.parent_id == self.env.user.employee_id:
            self.manager_is_user = True
        else:
            self.manager_is_user = False

    def set_to_confirm(self):
        if not self.deputation_line_ids:
            raise UserError(
                _("You Can't Confirm With Empty Lines, Please insert some lines.")
            )
        self.check_dates()
        self.state = "confirm"
        # self.activity_done()
        # # Sending Notification TO manager
        # self.activity_schedule(
        #     activity_type_id=self.env.ref(
        #         "self_service.mail_act_employee_deput"
        #     ).id,
        #     summary=_("New Deputation Needs Approve"),
        #     user_id=self.employee_id.parent_id.user_id.id,
        # )

    def set_to_draft(self):
        self.state = "draft"

    def set_to_audit(self):
        # if not self.env.user.has_group("group_audit_employee_deput"):
        #     raise UserError(_("You are not allowed to audit this deputation"))
        self.state = "audit"
        # self.activity_done()
        # for user in self.env["res.users"].search([]):
        #     if user.has_group("jes_hr_training.hr_managers_training"):
        #         self.activity_schedule(
        #             activity_type_id=self.env.ref(
        #                 "mail_act_employee_deput"
        #             ).id,
        #             summary=_("New Deputation Needs Approve"),
        #             user_id=user.id,
        #         )

    def set_to_approve(self):
        if self.employee_id.parent_id.id != self.env.user.employee_id.id:
            raise UserError(
                _("You're Not Allowed to Confirm. Only manager Can confirm.")
            )
        self.state = "approve1"
        # self.activity_done()
        # for user in self.env["res.users"].search([]):
        #     if user.has_group("second_approve_employee_deput"):
        #         self.activity_schedule(
        #             activity_type_id=self.env.ref(
        #                 "mail_act_employee_deput"
        #             ).id,
        #             summary=_("New Deputation Needs Approve"),
        #             user_id=user.id,
        #         )

    def set_to_approve2(self):
        self.state = "approve2"
        # self.activity_done()
        # for user in self.env["res.users"].search([]):
        #     if user.has_group("group_audit_employee_deput"):
        #         self.activity_schedule(
        #             activity_type_id=self.env.ref(
        #                 "mail_act_employee_deput"
        #             ).id,
        #             summary=_("New Deputation Needs Approve"),
        #             user_id=user.id,
        #         )

    def set_to_done(self):
        self.state = "done"
        # self.activity_done()

    def set_to_reject(self):
        self.state = "reject"
        # self.activity_done()

    def check_dates(self):
        for line in self.deputation_line_ids:
            if line.date_to < line.date_from:
                raise UserError(_("End Date must be greater than or equal Start date"))

    # set all current running activities to done
    def activity_done(self):
        for rec in self.activity_ids:
            rec.action_done()

    def action_confirm(self):
        self.state = "confirm"

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code(
            "deputation.request"
        ) or _("New")
        return super(EmployeeDeputation, self).create(values)


class DeputationLine(models.Model):
    _name = "deputation.request.line"

    deputation_request_id = fields.Many2one(
        comodel_name="emp.deputation.request", string="Insurance"
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        related="deputation_request_id.employee_id",
        string="Employee",
    )
    state = fields.Selection(related="deputation_request_id.state", store=True)
    request_type = fields.Selection(
        string="Travel Type",
        required=True,
        selection=[("internal", "Internal"), ("external", "External")],
        default="internal",
    )
    external_id = fields.Many2one("external.actors", string="External Site")
    country_id = fields.Many2one("res.country", string="Country")
    state_id = fields.Many2one("res.country.state", string="City")
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    safe_house = fields.Boolean("Safe House", default=False)
    safe_food = fields.Boolean("Safe Food", default=False)
    trans_allowance = fields.Boolean("Transportation Allowance", default=False)
    safe_ticket = fields.Float("Safe Ticket")
    total_allowance = fields.Float(
        "Total Allowances", compute="compute_total_allowance", compute_sudo=True
    )
    number_of_days = fields.Integer(
        string="Number Of Days", required=False, compute="compute_total_allowance"
    )
    cost_days = fields.Integer(
        string="Cost depend on Days", required=False, compute="compute_total_allowance"
    )

    @api.constrains("date_from", "date_to", "external_id", "total_allowance")
    def _get_constrains(self):
        for record in self:
            if record.deputation_request_id.request_need_id:
                employee_deputation = record.deputation_request_id.request_need_id.deputation_request_line_ids.filtered(
                    lambda l: l.employee_id == record.deputation_request_id.employee_id
                )
                if (
                    record.deputation_request_id.employee_id.id
                    not in employee_deputation.employee_id.ids
                ):
                    raise ValidationError(_("You can't Change Employee Name"))
                if record.deputation_request_id.mission != employee_deputation.mission:
                    raise ValidationError(_("You can't Change Mission"))
                if record.date_to > employee_deputation.date_to:
                    raise ValidationError(
                        _("You can't Make Date Bigger Than Need Request Date")
                    )
                if record.total_allowance > employee_deputation.cost_without_allowances:
                    raise ValidationError(
                        _("You can't Make Amount Bigger Than Need Request Amount")
                    )
                if record.request_type != employee_deputation.dep_request_type:
                    raise ValidationError(_("You can't Change Request Type"))
                if record.country_id.id != employee_deputation.country_id.id:
                    raise ValidationError(_("You can't Change Country"))
                if record.external_id != employee_deputation.external_id:
                    raise ValidationError(_("You can't Change Country"))

    @api.onchange("request_type")
    def onchange_request_type(self):
        self.country_id = False
        self.external_id = False

    @api.depends(
        "deputation_request_id.grade_id",
        "safe_food",
        "safe_house",
        "safe_food",
        "country_id",
        "request_type",
        "date_from",
        "date_to",
        "trans_allowance",
    )
    def compute_total_allowance(self):
        for rec in self:
            if not rec.trans_allowance:
                trans = (rec.deputation_request_id.employee_id.hr_grade.transport) / 30
            else:
                trans = 0
            if rec.date_from and rec.date_to:
                number_of_days = cost_days = (rec.date_to - rec.date_from).days + 1
                if rec.request_type == "internal":
                    amount = (
                        rec.deputation_request_id.sudo().grade_id.internal_secondment
                    )
                    cost_days += 2
                else:
                    number_of_days += (
                        rec.country_id.days_after + rec.country_id.days_before
                    )
                    if not rec.country_id or not rec.country_id.country_degree:
                        amount = 0
                    else:
                        if rec.country_id.country_degree == "first":
                            amount = (
                                rec.deputation_request_id.sudo().grade_id.outside_a_secondment
                            )
                        elif rec.country_id.country_degree == "second":
                            amount = (
                                rec.deputation_request_id.sudo().grade_id.outside_b_secondment
                            )
                        elif rec.country_id.country_degree == "third":
                            amount = (
                                rec.deputation_request_id.sudo().grade_id.outside_c_secondment
                            )
                        else:
                            amount = (
                                rec.deputation_request_id.sudo().grade_id.outside_hard_secondment
                            )
            else:
                amount = 0
                number_of_days = cost_days = 0
            rec.number_of_days = number_of_days
            rec.cost_days = cost_days
            deduct = 1
            if rec.safe_house or rec.safe_food:
                deduct = 0.5
            if rec.safe_food and rec.safe_house:
                deduct = 0.25
            trans_amount = trans * cost_days
            total_allowance = (amount * deduct * cost_days) + trans_amount
            if total_allowance > 0:
                rec.total_allowance = total_allowance
            else:
                rec.total_allowance = 0
