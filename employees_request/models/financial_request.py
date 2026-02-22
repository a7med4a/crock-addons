# -*- coding: utf-8 -*-آ1ى1

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions


class financial_request(models.Model):
    _name = "emp.financial.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Financial Request"

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(financial_request, self).unlink()

    insurance_card_num = fields.Char(string="Insurance Card#", required=False)
    iban_number = fields.Char(
        string="IBAN Number", related="employee_id.iban_number", required=False
    )
    bank_id = fields.Many2one(
        comodel_name="res.bank",
        related="employee_id.bank_id",
        string="Bank Name",
        required=False,
    )
    amount = fields.Float(string="Amount", required=False)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    phone = fields.Char(string="Phone", required=False)
    is_dependents = fields.Boolean(string="Dependents")
    related_attach = fields.Many2many(
        "ir.attachment", string="Attachment", ondelete="cascade"
    )

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "confirm"

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("financial.request") or _(
            "New"
        )
        return super(financial_request, self).create(values)
