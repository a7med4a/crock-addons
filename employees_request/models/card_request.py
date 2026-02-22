# -*- coding: utf-8 -*-

# Copyright 2021 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions


class card_request(models.Model):
    _name = "emp.card.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Card Request"

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(card_request, self).unlink()

    name = fields.Char(string="Name")
    request_type = fields.Selection(
        string="Request Type",
        selection=[
            ("New", "New"),
            ("Renewal", "Renewal"),
            ("Lost", "Lost replacement"),
            ("Damaged", "Damaged replacement"),
            ("Editing-Data", "Editing Data"),
        ],
        default="New",
        required=True,
    )
    job_title = fields.Char(
        string="Job Position", related="employee_id.job_title", required=False
    )
    employee_code = fields.Char(
        string="Employee Code", related="employee_id.pin", required=False
    )
    request_num = fields.Integer(
        string="Request Number",
        compute="_compute_request_num",
        required=False,
        store=True,
    )

    @api.depends("employee_id")
    def _compute_request_num(self):
        for rec in self:
            rec.request_num = rec.env["emp.card.request"].search_count(
                [
                    ("employee_id", "=", rec.employee_id.id),
                    ("state", "in", ("confirm", "Approved")),
                ]
            )

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "confirm"

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("card.request") or _(
            "New"
        )
        return super(card_request, self).create(values)

    def action_reprint(self):
        return self.env.ref(
            "employees_request.action_print_employee_card"
        ).report_action(self)
