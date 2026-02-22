from odoo import models, api, fields
import time
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime


class EmpAbsInternalReqest(models.AbstractModel):
    _name = "emp.internal.request"
    _inherit = "jes.hr.access.abstract"

    name = fields.Char(string="Name", required=False)
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        default=lambda self: self.env.user.employee_id,
    )
    identification_id = fields.Char(
        string="Identification No",
        related="employee_id.identification_id",
        required=False,
    )
    passport_id = fields.Char(
        string="Passport No", related="employee_id.passport_id", required=False
    )
    description = fields.Text(string="Description", required=False)
    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("confirm", "Submitted"),
            ("Approved", "Approved"),
            ("cancel", "Cancel"),
            ("refuse", "Refused"),
        ],
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

    emp_readonly = fields.Boolean(
        string="Make employee Readonly", compute="_compute_field_readonly", store=True
    )

    def action_reset_draft(self):
        self.write({"state": "draft"})

    def action_emp_req_refuse(self):
        self.write({"state": "refuse"})

    def action_emp_req_cancel(self):
        self.write({"state": "cancel"})

    @api.depends("employee_id")
    def _compute_field_readonly(self):
        # for record in self:
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

    # @api.depends("employee_id")
    # @api.depends("employee_id")
    # def _compute_field_readonly(self):
    #     for record in self:
    #         ss_group = self.env.user.has_group(
    #             "employees_request.group_self_services_request"
    #         )
    #         admin_group = self.env.user.has_group(
    #             "employees_request.emp_request_access_group_admin"
    #         )
    #
    #         if ss_group and not admin_group:
    #             record.emp_readonly = True
    #         else:
    #             record.emp_readonly = False

    def action_confirm(self):
        self.state = "confirm"

    def action_Approved(self):
        self.state = "Approved"
        self.activity_schedule(
            "approvals_management.mng_activity_data_approval",
            note=_(
                "welcome , \n Your request is Accepted ( %s #: %s Request date: %s )"
            )
            % (self._description, self.name, self.request_date),
            user_id=self.employee_id.user_id.id,
        )
