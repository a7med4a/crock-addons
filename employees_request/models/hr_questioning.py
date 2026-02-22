from datetime import timedelta

from bs4 import BeautifulSoup
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class Questioning(models.Model):
    _name = "hr.questioning"
    _description = "Questioning"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "sequence"
    _order = "id desc"

    employee_to_questioning = fields.Boolean(compute="compute_employee_to_questioning")
    justified = fields.Boolean()
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        states={
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "man_validate": [("readonly", True)],
            "hr_validate": [("readonly", True)],
            "done": [("readonly", True)],
        },
        tracking=True,
        required=True,
    )
    state = fields.Selection(
        [
            ("draft", "تحت المراجعة"),
            ("confirm", "إبداء الرأي"),
            ("refuse", "Refused"),
            ("man_validate", "Manager Approve"),
            ("hr_validate", "HR Approve"),
            ("done", "Done"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        tracking=True,
        default="draft",
    )
    questioning_type = fields.Selection(
        [("late", "Late"), ("absence", "Absence"), ("violation", "Violation")],
        string="Questioning Type",
        required=True,
        default="violation",
        states={
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "man_validate": [("readonly", True)],
            "done": [("readonly", True)],
            "hr_validate": [("readonly", True)],
        },
    )
    absence_days = fields.Integer(
        "ايام الغياب",
        states={
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "man_validate": [("readonly", True)],
            "done": [("readonly", True)],
            "hr_validate": [("readonly", True)],
        },
    )
    late_minutes = fields.Integer(
        "دقائق التاخير",
        states={
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "man_validate": [("readonly", True)],
            "done": [("readonly", True)],
            "hr_validate": [("readonly", True)],
        },
    )
    penalty_class = fields.Many2one(
        "hr.penalty.class",
        string="Penalty Class",
        states={
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "man_validate": [("readonly", True)],
            "done": [("readonly", True)],
            "hr_validate": [("readonly", True)],
        },
    )
    penalty = fields.Many2one(
        "hr.penalty",
        string="Penalty",
        states={
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "man_validate": [("readonly", True)],
            "done": [("readonly", True)],
            "hr_validate": [("readonly", True)],
        },
    )
    reason = fields.Text(
        tracking=True,
        string="Employee justification",
    )
    violation_reason = fields.Text(
        tracking=True,
        string="Violation Reason",
        states={
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "man_validate": [("readonly", True)],
            "done": [("readonly", True)],
            "hr_validate": [("readonly", True)],
            "draft": [("readonly", False)],
        },
    )
    complete_name = fields.Char(
        "Full Location Name", compute="_compute_complete_name", store=True
    )
    first_approver_id = fields.Many2one(
        "hr.employee",
        string="First Approval",
        readonly=True,
        copy=False,
        help="This area is automatically filled by the user who validate",
    )
    second_approver_id = fields.Many2one(
        "hr.employee",
        string="Second Approval",
        readonly=True,
        copy=False,
        help="This area is automatically filled by the user who validate",
    )
    first_approver_choice = fields.Char(readonly=True)
    second_approver_choice = fields.Char(readonly=True)

    penalty_date = fields.Date(string="Penalty Date")
    penalty_month = fields.Selection(
        [
            ("1", "January"),
            ("2", "February"),
            ("3", "March"),
            ("4", "April"),
            ("5", "May"),
            ("6", "June"),
            ("7", "July"),
            ("8", "August"),
            ("9", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        string="Month",
    )
    number_of_minutes = fields.Float(string="Number of Minutes", digits=(16, 0))
    penalty_code = fields.Integer(string="Code", related="penalty.code")
    penalty_class_code = fields.Integer(string="Code", related="penalty_class.code")
    number_repeating = fields.Integer()
    days_in_month = fields.Html(required=0)
    date_start = fields.Date()
    date_end = fields.Date()
    submit_date = fields.Date()
    due_date = fields.Date(string="Due Date", compute="_compute_due_date", store=True)
    is_past_due = fields.Boolean(compute="_compute_is_past_due", store=False)

    @api.depends("due_date")
    def _compute_is_past_due(self):
        today = fields.Date.today()
        for rec in self:
            if rec.due_date and rec.due_date < today:
                rec.is_past_due = True
            else:
                rec.is_past_due = False

    @api.depends("submit_date")
    def _compute_due_date(self):
        for record in self:
            if record.submit_date:
                date = record.submit_date
                added_days = 0
                while added_days < 3:
                    date += timedelta(days=1)
                    if date.weekday() not in (4, 5):
                        added_days += 1
                record.due_date = date
            else:
                record.due_date = False

    @api.depends("employee_id", "questioning_type")
    def _compute_complete_name(self):
        for rec in self:
            if rec.employee_id:
                rec.complete_name = "%s" % (rec.employee_id.name)

    def action_confirm(self):
        self.write({"state": "confirm"})
        return True

    def action_submit(self):
        self.write({"state": "man_validate"})

    def action_approve(self):
        self.write(
            {
                "state": "hr_validate",
                "first_approver_id": self.env.user.employee_id.id,
                "first_approver_choice": "سبب مقبول",
            }
        )

    def action_question_refuse(self):
        if self.employee_id.parent_id.user_id.id != self.env.user.id:
            pass
            # raise UserError(_("You Can not Refuse Request"))
        else:
            current_employee = self.env.user.employee_id
            self.write(
                {
                    "state": "hr_validate",
                    "first_approver_id": current_employee.id,
                    "first_approver_choice": "سبب مرفوض",
                }
            )

            self.activity_done()

    def hr_approve(self):
        current_employee = self.env.user.employee_id
        self.activity_done()
        self.write(
            {
                "state": "done",
                "second_approver_id": current_employee.id,
                "second_approver_choice": "سبب مقبول",
            }
        )
        self.activity_done()

    def compute_employee_to_questioning(self):
        for rec in self:
            if rec.employee_id.user_id.id == self.env.user.id:
                rec.employee_to_questioning = 1
            else:
                rec.employee_to_questioning = 0

    def approve_justification(self):
        for rec in self:
            if rec.reason:
                activity_type = self.env.ref(
                    "employees_request.mng_activity_hr_questioning"
                )
                model_id = (
                    self.env["ir.model"]
                    .search([("model", "=", "hr.questioning")], limit=1)
                    .id
                )
                self.env["mail.activity"].create(
                    {
                        "summary": "لقد قام الموظف بكتابه التبرير الخاص به",
                        "activity_type_id": activity_type.id,
                        "res_model_id": model_id,
                        "res_id": self.id,
                        "user_id": self.employee_id.user_id.id,
                    }
                )
                rec.justified = 1
            else:
                raise ValidationError(_("You Did not write Your Justification"))

    def action_submet(self):
        summary = f" نحتاج من سيادتكم القيام بكتابه التبرير للمسائله {self.sequence} وفى حاله عدم القيام بذلك خلال ثلاثه ايام سوف نقوم بتطبيق العقوبه"
        activity_type = self.env.ref("employees_request.mng_activity_hr_questioning")
        model_id = (
            self.env["ir.model"].search([("model", "=", "hr.questioning")], limit=1).id
        )
        self.env["mail.activity"].create(
            {
                "summary": summary,
                "activity_type_id": activity_type.id,
                "res_model_id": model_id,
                "res_id": self.id,
                "user_id": self.employee_id.user_id.id,
            }
        )
        self.submit_date = fields.Date.today()
        return super(Questioning, self).action_submet()

    def hr_refuse(self):
        self.activity_done()
        current_employee = self.env.user.employee_id

        self.write({"state": "refuse"})
        self.write(
            {
                "state": "done",
                "second_approver_id": current_employee.id,
                "second_approver_choice": "سبب مرفوض",
            }
        )
        self.activity_done()

    # set all current running activities to done
    def activity_done(self):
        for rec in self.activity_ids:
            rec.action_done()

    def unlink(self):
        for rec in self:
            if rec.state == "done":
                raise ValidationError(_("you cannot delete with 'approved' status ! "))
            return super().unlink()

    sequence = fields.Char(
        string="Sequence",
        readonly=True,
        copy=False,
        default=lambda self: _("New"),
    )

    @api.model
    def create(self, vals):
        if vals.get("sequence", _("New")) == _("New"):
            vals["sequence"] = self.env["ir.sequence"].next_by_code(
                "hr.questioning.sequence"
            ) or _("New")
        return super().create(vals)
