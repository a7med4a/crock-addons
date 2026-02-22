from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class HrPermission(models.Model):
    _inherit = "hr.permission"
    _description = "Permission Request"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        # readonly=True,
        default=lambda self: self.env.user.employee_id,
    )

    emp_readonly = fields.Boolean(
        string="Make employee Readonly", compute="_compute_field_readonly", store=True
    )

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

            # if ss_group and not admin_group:
            #     record.emp_readonly = True
            # else:
            #     record.emp_readonly = False
