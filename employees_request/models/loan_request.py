# -*- coding: utf-8 -*-آ1ى1

from odoo import _, api, fields, models, exceptions


class HrLoan(models.Model):
    _inherit = "hr.loan"

    emp_readonly = fields.Boolean(
        string="Make employee Readonly", compute="_compute_field_readonly", store=True
    )

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(HrLoan, self).unlink()

    # @api.depends("employee_id")
    # def _compute_field_readonly(self):
    #     for record in self:
    #         ss_group = self.env.user.has_group(
    #             "employees_request.group_self_services_request"
    #         )
    #         admin_group = self.env.user.has_group(
    #             "employees_request.emp_request_access_group_admin"
    #         )
    #         if ss_group and not admin_group:
    #             record.emp_readonly = True
    #         else:
    #             record.emp_readonly = False
    @api.depends("employee_id")
    def _compute_field_readonly(self):
        for record in self:
            ss_group = self.env.user.has_group(
                "employees_request.group_self_services_request"
            )
            admin_group = self.env.user.has_group(
                "employees_request.emp_request_access_group_admin"
            )
            if self.env.user.has_group(
                "employees_request.emp_request_access_group_admin"
            ):
                self.emp_readonly = 0
            else:
                self.emp_readonly = 1
