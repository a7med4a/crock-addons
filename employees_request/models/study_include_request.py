# -*- coding: utf-8 -*-

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions


class study_include_request(models.Model):
    _name = "emp.study_include.request"
    _inherit = [
        "emp.internal.request",
        "approval.order",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _description = "Add certification"

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(study_include_request, self).unlink()

    study_type = fields.Selection(
        string="Study Type",
        selection=[
            ("Presence", "Presence"),
            ("Online", "Online"),
            ("Online_Presenc", "Online & Presence"),
        ],
        required=True,
    )
    study_include_authority = fields.Char(string="Study authority", required=True)
    date_from = fields.Date(string="Date From", required=False)
    date_to = fields.Date(string="Date To", required=False)
    certification_date = fields.Date(string="Certification Date", required=True)
    day_number = fields.Integer(
        string="Days Number", required=False, compute="_compute_day_number"
    )

    certification_level_id = fields.Many2one(
        comodel_name="certification.level", string="Certification Level", required=True
    )
    study_include_field_id = fields.Many2one(
        comodel_name="study.field", string="Study Field", required=True
    )
    related_attach = fields.Many2many(
        "ir.attachment", string="Attachment", required=True, ondelete="cascade"
    )

    job_id = fields.Many2one("hr.job", string="Job")
    department_id = fields.Many2one("hr.department", string="Department")

    @api.onchange("request_date", "employee_id", "study_type")
    def onchange_request_date(self):
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    @api.onchange("date_from", "date_to")
    def _onchange_dates(self):
        for rec in self:
            if rec.date_to and rec.date_from and rec.date_to < rec.date_from:
                raise exceptions.ValidationError(
                    _("Date To Must be grater than Date From")
                )

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

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "confirm"

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code(
            "study_include.request"
        ) or _("New")
        attach = values.get("related_attach", False)
        has_attch = attach[0][2]
        if not has_attch:
            raise exceptions.ValidationError(_("You Must set Attachment"))
        return super(study_include_request, self).create(values)
