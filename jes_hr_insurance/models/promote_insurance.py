from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class InsurancePromote(models.Model):
    _name = "insurance.promote"
    _description = "Insurance Promotion"
    _rec_name = "emp_id"

    code = fields.Char(string="Request No", readonly=True, copy=False)
    promotion_date = fields.Date(
        string="Promotion Date",
        required=True,
        default=fields.Date.context_today,
        states={
            "cancel": [("readonly", True)],
            "done": [("readonly", True)],
            "sent": [("readonly", True)],
        },
    )
    sending_date = fields.Date(
        string="Sending Date",
        required=True,
        default=fields.Date.context_today,
        states={
            "cancel": [("readonly", True)],
            "done": [("readonly", True)],
            "sent": [("readonly", True)],
            "open": [("readonly", True)],
        },
    )
    emp_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        states={
            "cancel": [("readonly", True)],
            "done": [("readonly", True)],
            "sent": [("readonly", True)],
            "open": [("readonly", True)],
        },
    )
    current_categ = fields.Many2one("insurance.categ", string="Current Category")
    new_categ = fields.Many2one(
        "insurance.categ",
        string="New Category",
        required=True,
        states={
            "cancel": [("readonly", True)],
            "done": [("readonly", True)],
            "sent": [("readonly", True)],
            "open": [("readonly", True)],
        },
    )
    state = fields.Selection(
        [
            ("draft", "Unsent"),
            ("cancel", "Cancelled"),
            ("open", "Requested"),
            ("sent", "Sent"),
            ("done", "Added"),
        ],
        string="Status",
        default="draft",
        readonly=True,
        copy=False,
    )

    def action_request(self):
        self.state = "open"

    @api.model
    def create(self, vals):
        insurance = self.env["insurance.add.delete"].search(
            [("emp_id", "=", vals.get("emp_id"))], limit=1, order="id desc"
        )
        if insurance:
            res = super(InsurancePromote, self).create(vals)
            return res
        else:
            raise ValidationError(_("No Insurances for this employee!"))

    def action_cancel(self):
        self.state = "cancel"

    # cron_job will promote when date come
    def auto_promote(self):
        requests = self.search(
            [("state", "=", "sent"), ("promotion_date", "<=", fields.Date.today())]
        )
        for res in requests:
            res.state = "done"
            if res.current_categ:
                insurance = self.env["insurance.add.delete"].search(
                    [
                        ("emp_id", "=", res.emp_id.id),
                        ("medical_insurance_id", "=", res.current_categ.id),
                    ],
                    limit=1,
                    order="id desc",
                )
                if insurance:
                    # delete
                    if res.emp_id.family_ids:
                        insurance_add_delete = self.env["insurance.add.delete"].create(
                            {
                                "emp_id": res.emp_id.id,
                                "request_type": "delete",
                                "is_dependent": True,
                                "request_date": res.promotion_date,
                                "insurance_policy": insurance.insurance_policy.id,
                                "family_ids": [
                                    (4, x.id) for x in res.emp_id.family_ids
                                ],
                            }
                        )
                        insurance_add_delete.action_confirm()
                    else:
                        insurance_add_delete = self.env["insurance.add.delete"].create(
                            {
                                "emp_id": res.emp_id.id,
                                "request_type": "delete",
                                "is_dependent": False,
                                "request_date": res.promotion_date,
                                "insurance_policy": insurance.insurance_policy.id,
                            }
                        )
                        insurance_add_delete.action_confirm()
                    # add
                    if res.emp_id.family_ids:

                        insurance_add_delete = self.env["insurance.add.delete"].create(
                            {
                                "emp_id": res.emp_id.id,
                                "request_type": "add",
                                "is_dependent": True,
                                "request_date": res.promotion_date,
                                "insurance_policy": insurance.insurance_policy.id,
                                "medical_insurance_id": res.new_categ.id,
                                "family_ids": [
                                    (4, x.id) for x in res.emp_id.family_ids
                                ],
                            }
                        )
                        insurance_add_delete.action_confirm()
                    else:
                        insurance_add_delete = self.env["insurance.add.delete"].create(
                            {
                                "emp_id": res.emp_id.id,
                                "request_type": "add",
                                "is_dependent": False,
                                "request_date": res.promotion_date,
                                "insurance_policy": insurance.insurance_policy.id,
                                "medical_insurance_id": res.new_categ.id,
                            }
                        )
                        insurance_add_delete.action_confirm()
                return res
            else:
                raise ValidationError(_("No Insurances for this employee!"))


    def action_confirm(self):
        for res in self:
            if res.current_categ:
                insurance = self.env["insurance.add.delete"].search(
                    [
                        ("emp_id", "=", res.emp_id.id),
                        ("medical_insurance_id", "=", res.current_categ.id),
                    ],
                    limit=1,
                    order="id desc",
                )
                if insurance:
                    res.state = "sent"
                    res.code = self.env["ir.sequence"].next_by_code("promote.number")
                else:
                    raise ValidationError(_("No Insurances for this employee!"))
            else:
                raise ValidationError(_("No Insurances for this employee!"))

    def set_draft(self):
        self.state = "draft"

    @api.onchange("emp_id")
    def _compute_categ(self):
        for rec in self:
            add_delete_rec = self.env["insurance.add.delete"].search(
                [("emp_id", "=", rec.emp_id.id)], limit=1, order="id desc"
            )
            if add_delete_rec and add_delete_rec.medical_insurance_id:
                categ = self.env["insurance.categ"].browse(
                    add_delete_rec.medical_insurance_id.id
                )
                rec.current_categ = categ.id
            # else:
            #     rec.current_categ = False
