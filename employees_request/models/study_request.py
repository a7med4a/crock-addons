# -*- coding: utf-8 -*-آ1ى1

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions


class certification(models.Model):
    _name = "certification.level"
    _rec_name = "name"
    _description = "Certification level"

    name = fields.Char()


class StudyField(models.Model):
    _name = "study.field"
    _rec_name = "name"
    _description = "study field"

    name = fields.Char()


class study_request(models.Model):
    _name = "emp.study.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Study Request"

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(study_request, self).unlink()

    study_type = fields.Selection(
        string="Study Type",
        selection=[
            ("Part-time", "Part-Time"),
            ("Full-Time", "Full-Time"),
            ("Online", "Online"),
        ],
        required=False,
    )
    study_period = fields.Selection(
        string="Study Period",
        selection=[("Morning", "Morning"), ("Evening", "Evening")],
        required=True,
    )
    study_authority = fields.Char(string="Study authority", required=True)
    date_from = fields.Date(string="Date From", required=False)
    date_to = fields.Date(string="Date To", required=False)
    day_number = fields.Integer(
        string="Days Number", required=False, compute="_compute_day_number"
    )

    certification_level_id = fields.Many2one(
        comodel_name="certification.level", string="Certification Level", required=True
    )
    study_field_id = fields.Many2one(
        comodel_name="study.field", string="Study Field", required=True
    )

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
        values["name"] = self.env["ir.sequence"].next_by_code("study.request") or _(
            "New"
        )
        return super(study_request, self).create(values)
