# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    req_salary_acc_debit_id = fields.Many2one(
        comodel_name="account.account", string="Salary Debit Account"
    )
    req_salary_acc_credit_id = fields.Many2one(
        comodel_name="account.account", string="Salary Credit Account"
    )
    req_salary_journal_id = fields.Many2one(
        comodel_name="account.journal", string="Salary Jornal"
    )

    req_leave_acc_debit_id = fields.Many2one(
        comodel_name="account.account", string="Leave Debit Account"
    )
    req_leave_acc_credit_id = fields.Many2one(
        comodel_name="account.account", string="Leave Credit Account"
    )
    req_leave_journal_id = fields.Many2one(
        comodel_name="account.journal", string="Leave Journal"
    )

    req_overtime_acc_debit_id = fields.Many2one(
        comodel_name="account.account", string="Overtime Debit Account"
    )
    req_overtime_acc_credit_id = fields.Many2one(
        comodel_name="account.account", string="Overtime Credit Account"
    )
    req_overtime_journal_id = fields.Many2one(
        comodel_name="account.journal", string="Overtime Journal"
    )

    req_hous_acc_debit_id = fields.Many2one(
        comodel_name="account.account", string="Housing Debit Account"
    )
    req_hous_acc_credit_id = fields.Many2one(
        comodel_name="account.account", string="Housing Credit Account"
    )
    req_hous_journal_id = fields.Many2one(
        comodel_name="account.journal", string="Housing Journal"
    )

    req_endserv_acc_debit_id = fields.Many2one(
        comodel_name="account.account", string="End of Service Debit Account"
    )
    req_endserv_acc_credit_id = fields.Many2one(
        comodel_name="account.account", string="End of Service Account"
    )
    req_endserv_journal_id = fields.Many2one(
        comodel_name="account.journal", string="End of Service Journal"
    )
    contract_expire_days_num = fields.Integer(
        string="Contract Expire Days", required=False, default=90
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    req_salary_acc_debit_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.req_salary_acc_debit_id",
        readonly=False,
        string="Debit Account",
    )
    req_salary_acc_credit_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.req_salary_acc_credit_id",
        readonly=False,
        string="Credit Account",
    )
    req_salary_journal_id = fields.Many2one(
        comodel_name="account.journal",
        related="company_id.req_salary_journal_id",
        readonly=False,
        string="Journal",
    )

    req_leave_acc_debit_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.req_leave_acc_debit_id",
        readonly=False,
        string=" Debit Account",
    )
    req_leave_acc_credit_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.req_leave_acc_credit_id",
        readonly=False,
        string=" Credit Account",
    )
    req_leave_journal_id = fields.Many2one(
        comodel_name="account.journal",
        related="company_id.req_leave_journal_id",
        readonly=False,
        string="Journal",
    )

    req_overtime_acc_debit_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.req_overtime_acc_debit_id",
        readonly=False,
        string=" Debit Account",
    )
    req_overtime_acc_credit_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.req_overtime_acc_credit_id",
        readonly=False,
        string=" Credit Account",
    )
    req_overtime_journal_id = fields.Many2one(
        comodel_name="account.journal",
        related="company_id.req_overtime_journal_id",
        readonly=False,
        string="Journal",
    )

    req_hous_acc_debit_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.req_hous_acc_debit_id",
        readonly=False,
        string=" Debit Account",
    )
    req_hous_acc_credit_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.req_hous_acc_credit_id",
        readonly=False,
        string=" Credit Account",
    )
    req_hous_journal_id = fields.Many2one(
        comodel_name="account.journal",
        related="company_id.req_hous_journal_id",
        readonly=False,
        string="Journal",
    )

    req_endserv_acc_debit_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.req_endserv_acc_debit_id",
        readonly=False,
        string=" Debit Account",
    )
    req_endserv_acc_credit_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.req_endserv_acc_credit_id",
        readonly=False,
        string=" Credit Account",
    )
    req_endserv_journal_id = fields.Many2one(
        comodel_name="account.journal",
        related="company_id.req_endserv_journal_id",
        readonly=False,
        string="Journal",
    )

    contract_expire_days_num = fields.Integer(
        string="Contract Expire Days",
        readonly=False,
        related="company_id.contract_expire_days_num",
    )
    ticket_request_debit_account_id = fields.Many2one(
        "account.account", string="Ticket Request Debit Account"
    )
    request_need_debit_account_id = fields.Many2one(
        "account.account", string="Request Need Debit Account"
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            {
                "ticket_request_debit_account_id": int(
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("ticket_request_debit_account_id")
                ),
                "request_need_debit_account_id": int(
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("request_need_debit_account_id")
                ),
            }
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "ticket_request_debit_account_id", self.ticket_request_debit_account_id.id
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "request_need_debit_account_id", self.request_need_debit_account_id.id
        )
