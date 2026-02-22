# -*- coding: utf-8 -*-
# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError, Warning, AccessError
from odoo.exceptions import UserError, ValidationError

from odoo.tools import float_is_zero, float_compare
from itertools import groupby

import json


class attendance_exception_request(models.Model):
    _name = "attendance.exception.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Attendance Exception Request"

    name = fields.Char(string="Name", required=False)
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        default=lambda self: self.env.user.employee_id,
    )
    description = fields.Text(string="Reason", required=False)
    state = fields.Selection(
        string="State",
        selection=[("draft", "Draft"), ("confirm", "Confirm")],
        default="draft",
        required=False,
        tracking=True,
    )
    request_date = fields.Date(
        string="Request Date",
        required=True,
        tracking=True,
        readonly=True,
        default=fields.Date.context_today,
        states={"draft": [("readonly", False)]},
    )
    attendance_lines = fields.Many2many(
        comodel_name="hr.attendance", string="Exception Attendance Lines"
    )

    def action_confirm(self):
        self.state = "confirm"


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def check_from_select(self, emp_ids):
        emp_obj = self.browse(emp_ids)
        if emp_obj:
            emp_id = emp_obj[0].employee_id.id
            for rec in emp_obj:
                if rec.employee_id.id != emp_id:
                    raise ValidationError(
                        "The selected Lines Must be with rhe same employee"
                    )

    def exception_request(self):
        view_id = self.env.ref("employees_request.attendance_exception_view").id
        active_ids = self._context.get("active_ids") or []
        self.check_from_select(active_ids)
        return {
            "name": _("Attendance Exception"),
            "type": "ir.actions.act_window",
            "res_model": "attendance.exception.wizard",
            "view_mode": "form",
            "view_id": view_id,
            "target": "new",
            "context": {"default_attendance_lines": [(6, 0, active_ids)]},
        }
