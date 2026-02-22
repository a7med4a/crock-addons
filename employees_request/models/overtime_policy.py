# -*- coding: utf-8 -*-آ1ى1

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions


class OvertimePolicy(models.Model):
    _name = "overtime.policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def unlink(self):
        if self.filtered(lambda r: r.state != "draft"):
            raise exceptions.ValidationError(
                _("You can't delete overtime policy not draft state")
            )
        return super(OvertimePolicy, self).unlink()

    state = fields.Selection(
        string="Status",
        selection=[("draft", "Draft"), ("confirm", "Confirmed")],
        required=False,
        default="draft",
    )
    name = fields.Char(string="Policy", required=True)
    normal_hour_rate = fields.Float(string="Normal Hour Rate", required=False)
    max_normal_hour = fields.Float(string="Max Normal Hour", required=False)
    public_hour_rate = fields.Float(string="Public Hour Rate", required=False)
    max_public_hour = fields.Float(string="Max Public Hour", required=False)
    weekend_hour_rate = fields.Float(string="Weekend Hour Rate", required=False)
    max_weekend_hour = fields.Float(string="Max Weekend Hour", required=False)
    salary_structure_id = fields.Many2one(
        comodel_name="hr.payroll.structure", string="Salary Structure", required=False
    )
    calc_type = fields.Selection(
        string="Calculation Based On",
        selection=[("basic", "Basic"), ("basic_allowance", "Basic and Allowances")],
        required=False,
        default="basic",
    )
    non_calc_allowance_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="overtime_policy_salary_rule_fields",
        string="Non Calc Allowances",
        domain="[('model', '=', 'hr.contract'), ('name', 'in', ('housing', 'other_allowance', 'transportation')), ('ttype', '=', 'monetary')]",
    )

    def action_confirm(self):
        self.write({"state": "confirm"})

    def action_reset_draft(self):
        self.write({"state": "draft"})
