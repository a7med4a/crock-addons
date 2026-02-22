# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import except_orm, ValidationError
import time


class attendance_exception_wizard(models.TransientModel):
    _name = "attendance.exception.wizard"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        default=lambda self: self.env.user.employee_id,
    )
    description = fields.Text(string="Reason", required=True)
    request_date = fields.Date(
        string="Request Date",
        required=True,
        readonly=True,
        default=fields.Date.context_today,
    )
    attendance_lines = fields.Many2many(
        comodel_name="hr.attendance", string="Exception Attendance Lines"
    )

    def action_request(self):
        self.env["attendance.exception.request"].create(
            {
                "employee_id": self.employee_id.id,
                "description": self.description,
                "request_date": self.request_date,
                "attendance_lines": self.attendance_lines,
                "state": "draft",
            }
        )
