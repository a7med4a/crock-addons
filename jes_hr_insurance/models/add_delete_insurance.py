from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AddDeleteInsurance(models.Model):
    _name = "insurance.add.delete"
    _description = "Add or Delete insurance from employee"
    _rec_name = "emp_id"
    _order = "id desc"

    code = fields.Char(string="Request No", readonly=True, copy=False)
    emp_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,

    )
    insurance_policy = fields.Many2one(
        comodel_name="insurance.policy",
        compute="_compute_policy",
        string="Insurance Policy",
        required=False,
        store=True,
    )
    request_type = fields.Selection(
        string="Request Type",
        selection=[("add", "Add"), ("delete", "Delete")],
        required=True,

    )
    request_date = fields.Date(
        string="Request Date",
    )
    sending_date = fields.Date(
        string="Sending Date",
        required=True,
        default=fields.Date.context_today,

    )
    family_ids = fields.Many2many("hr.family", string="Family")
    is_dependent = fields.Boolean(
        "Dependent",

    )
    medical_insurance_id = fields.Many2one(
        "insurance.categ",
        compute="_compute_medical_category",
        string="Medical Category",
        store=True,
    )
    department_emp_ids = fields.Many2one(
        "hr.department", string="Department", related="emp_id.department_id"
    )

    state = fields.Selection(
        [
            ("draft", "Unsent"),
            ("cancel", "Cancelled"),
            ("open", "Requested"),
            ("done", "Added"),
        ],
        string="Status",
        default="draft",
        readonly=True,
        copy=False,
    )

    def action_request(self):
        self.state = "open"

    def action_cancel(self):
        self.state = "cancel"

    def action_confirm(self):
        for res in self:
            res.state = "done"
            res.code = self.env["ir.sequence"].next_by_code("add.number")
            if res.family_ids and res.request_type == "add" and res.is_dependent:
                res.emp_id.has_insurance = True
                res.emp_id.last_add_insurance = res.request_date
                res.emp_id.last_medical_insurance_id = res.medical_insurance_id.id
                res.emp_id.policy_id = res.insurance_policy.id

                for rec in res.family_ids:
                    rec.has_insurance = True
                    rec.last_add_insurance = res.request_date

            elif res.request_type == "add" and not res.is_dependent:

                res.emp_id.has_insurance = True
                res.emp_id.last_medical_insurance_id = res.medical_insurance_id.id
                res.emp_id.last_add_insurance = res.request_date
                res.emp_id.policy_id = res.insurance_policy.id

            elif (
                res.family_ids and res.request_type == "delete" and res.is_dependent
            ):

                if not res.emp_id.has_insurance:
                    raise UserError(_("NO Insurance for this Employee"))
                res.emp_id.has_insurance = False
                res.emp_id.last_delete_insurance = res.request_date
                for rec in res.family_ids:
                    rec.has_insurance = False
                    rec.last_delete_insurance = res.request_date
            elif res.request_type == "delete" and not res.is_dependent:
                if not res.emp_id.has_insurance:
                    raise UserError(_("NO Insurance for this Employee"))
                else:
                    if res.emp_id.family_ids:
                        for rec in res.emp_id.family_ids:
                            rec.has_insurance = False
                            rec.last_delete_insurance = res.request_date
                    res.emp_id.has_insurance = False
                    res.emp_id.last_delete_insurance = res.request_date

    def set_draft(self):
        self.state = "draft"

    @api.depends("emp_id")
    def _compute_medical_category(self):
        for rec in self:
            if rec.medical_insurance_id:
                continue
            # if rec.emp_id.last_medical_insurance_id:
            #     rec.medical_insurance_id = rec.emp_id.last_medical_insurance_id.id
            #     continue
            # if rec.emp_id.grade_id.medical_insurance_id:
            #     rec.medical_insurance_id = rec.emp_id.grade_id.medical_insurance_id.id
            else:
                medical_insurance = rec.emp_id.get_emp_medical_insurance()
                if medical_insurance:
                    rec.medical_insurance_id = medical_insurance.id
                else:
                    rec.medical_insurance_id = False

    @api.depends("emp_id", "request_date")
    def _compute_policy(self):
        for rec in self:
            if rec.insurance_policy:
                insurance = rec.insurance_policy
            else:

                insurance = self.env["insurance.policy"].search(
                    [
                        ("policy_start_date", "<=", rec.request_date),
                        ("policy_end_date", ">=", rec.request_date),
                    ],
                    limit=1,
                )

            if insurance:

                rec.insurance_policy = insurance.id

    @api.onchange("request_type", "emp_id")
    def onchange_request_type(self):
        if self.emp_id.family_ids:
            self.write({"family_ids": [(5, 0, 0)]})
            if self.request_type == "add":
                self.write(
                    {
                        "family_ids": [
                            (4, x.id)
                            for x in self.emp_id.family_ids
                            if not x.has_insurance
                        ]
                    }
                )
            elif self.request_type == "delete":
                self.write(
                    {
                        "family_ids": [
                            (4, x.id)
                            for x in self.emp_id.family_ids
                            if x.has_insurance
                        ]
                    }
                )

    # @api.model
    # def create(self, vals):
    #     res = super(AddDeleteInsurance, self).create(vals)
    #     res.code = self.env['ir.sequence'].next_by_code('add.number')
    #
    #     if res.dependent_ids and res.request_type == 'add' and res.is_dependent:
    #         res.emp_id.has_insurance = True
    #         res.emp_id.last_add_insurance = res.request_date
    #         res.emp_id.last_medical_insurance_id = res.medical_insurance_id.id
    #
    #         for rec in res.dependent_ids:
    #             rec.has_insurance = True
    #             rec.last_add_insurance = res.request_date
    #
    #     elif res.request_type == 'add' and not res.is_dependent:
    #
    #         res.emp_id.has_insurance = True
    #         res.emp_id.last_medical_insurance_id = res.medical_insurance_id.id
    #         res.emp_id.last_add_insurance = res.request_date
    #
    #     elif res.dependent_ids and res.request_type == 'delete' and res.is_dependent:
    #
    #         if not res.emp_id.has_insurance:
    #             raise UserError(
    #                 _('NO Insurance for this Employee'))
    #         res.emp_id.has_insurance = False
    #         res.emp_id.last_delete_insurance = res.request_date
    #         for rec in res.dependent_ids:
    #             rec.has_insurance = False
    #             rec.last_delete_insurance = res.request_date
    #     elif res.request_type == 'delete' and not res.is_dependent:
    #         if not res.emp_id.has_insurance:
    #             raise UserError(
    #                 _('NO Insurance for this Employee'))
    #         else:
    #             if res.emp_id.dependent_ids:
    #                 for rec in res.emp_id.dependent_ids:
    #                     rec.has_insurance = False
    #                     rec.last_delete_insurance = vals.get('request_date')
    #             res.emp_id.has_insurance = False
    #             res.emp_id.last_delete_insurance = res.request_date
    #
    #     return res

    # def write(self, vals):
    #     if vals.get('emp_id') or vals.get('request_date') or vals.get('request_type'):
    #         raise UserError(_('This Record Not Editable.'))
    #     return super(AddDeleteInsurance, self).write(vals)
