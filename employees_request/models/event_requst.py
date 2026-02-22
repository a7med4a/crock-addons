from odoo import models, _, api, fields, models, exceptions
import calendar
from datetime import datetime


class EmpEventRequest(models.Model):
    _name = "hr.event"
    _rec_name = "event_name"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Event Request"

    event_name = fields.Char(string="Event Name", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Team Leader",
        required=True,
        default=lambda self: self.env.user.employee_id,
    )
    description = fields.Text(string="Mission", required=True)
    event_line_ids = fields.One2many(
        comodel_name="hr.event.line",
        inverse_name="event_request_id",
        domain=[("state", "!=", "reject")],
        string="Employees",
        required=False,
    )

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(EmpEventRequest, self).unlink()

    def action_confirm(self):
        self.state = "confirm"

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("event.request") or _(
            "New"
        )
        return super(EmpEventRequest, self).create(values)


class EventRequestLine(models.Model):
    _name = "hr.event.line"
    _rec_name = "employee_id"
    _inherit = ["jes.hr.access.abstract", "mail.thread", "mail.activity.mixin"]

    event_request_id = fields.Many2one(
        comodel_name="hr.event", string="Event", required=True
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee", string="Employee", required=True
    )
    job_role = fields.Selection(
        string="Job Role",
        selection=[
            ("attend", "Attending conferences and exhibitions"),
            ("organizer", "Organizer"),
            ("trainer", "Trainer"),
        ],
        required=True,
    )
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    notes = fields.Char(string="Notes", required=False)
    event_value = fields.Float(string="Value", required=False)
    event_start_date = fields.Date(
        string="Event Start Date",
        related="event_request_id.start_date",
        store=True,
        readonly=True,
    )
    event_end_date = fields.Date(
        string="Event End Date",
        related="event_request_id.end_date",
        store=True,
        readonly=True,
    )
    event_employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Team Leader",
        related="event_request_id.employee_id",
        store=True,
        readonly=True,
    )
    event_description = fields.Text(
        string="Mission",
        related="event_request_id.description",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        string="Status",
        selection=[
            ("draft", "Waiting Approval"),
            ("reject", "Reject"),
            ("approve", "Approved"),
        ],
        default="draft",
    )

    job_id = fields.Many2one("hr.job", string="Job")
    department_id = fields.Many2one("hr.department", string="Department")

    @api.onchange("event_request_id", "employee_id")
    def onchange_request_date(self):
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    def action_confirm(self):
        self.state = "approve"

    def action_reject(self):
        self.state = "reject"
