# -*- coding: utf-8 -*-آ1ى1
from dateutil.relativedelta import relativedelta

# Copyright 2023 Ahmed Amen :  www.linkedin.com/in/ahmed-abdul-khaliq
##############################################################################
from odoo import _, api, fields, models, exceptions


class resignation_request(models.Model):
    _name = "emp.resignation.request"
    _inherit = ["emp.internal.request", "mail.thread", "mail.activity.mixin"]
    _description = "Resignation Request"

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise exceptions.ValidationError(_('You cannot delete records if they are in non-draft state'))
    #     return super(resignation_request, self).unlink()

    requested_by = fields.Selection(
        string="Requested By",
        selection=[("employee", "Employee"), ("hr", "HR")],
        required=False,
        default="employee",
    )
    employee_eos_reason = fields.Selection(
        [
            ("1", "الاستقالة"),
            ("2", "انتهاء مدة العقد المحدد المدة"),
            (
                "3",
                "بلوغ العامل سن التقاعد وفق ما تقضي به أحكام نظام التأمينات الاجتماعية، مالم تمتد مدة العقد المحدد المدة إلى ما بعد هذه السن",
            ),
            (
                "4",
                "فسخ العقد لأحد الأسباب الواردة في المادتين (75) ، (80) من نظام العمل",
            ),
            ("5", "ترك العامل العمل في الحالات الواردة في المادة (81) من نظام العمل"),
            (
                "6",
                "انقطاع العامل عن العمل بسبب مرضه لمدد تزيد في مجموعها على مئة وعشرين يوماً متقطعة أو متصلة خلال السنة الواحدة التي تبدأ من تاريخ أول إجازة مرضية",
            ),
            (
                "7",
                "عجز العامل عجزاً كلياً عن أداء العمل المتفق عليه، ويثبت ذلك بتقرير طبي معتمد",
            ),
            ("8", "وفاة العامل"),
            (
                "9",
                "إذا ألغت السلطات الحكومية المختصة رخصة عمل أو إقامة العامل غير السعودي أو قررت عدم تجديدها أو إبعاده عن البلاد",
            ),
            ("10", "إغلاق المنشأة نهائياً"),
            ("11", "إنهاء النشاط الذي يعمل فيه العامل، مالم يتفق على غير ذلك"),
            (
                "12",
                "طلب الإحالة إلى التقاعد قبل بلوغ السن النظامية حسب نظام التقاعد وموافقة صاحب الصلاحية على ذلك",
            ),
            (
                "13",
                "عدم الكفاءة لحصوله على تقويم أداء وظيفي بتقدير غير مُرضٍ ثلاث مرات متتالية بشرط ألا تقل مدة التقويم عن ( 18 ) ثمانية عشر شهراً، وأن يصدر في هذه الحالة قرار من صاحب الصلاحية",
            ),
            ("14", "فسخ العقد على المادة (77) من نظام العمل"),
        ],
        string="EOS Reason",
    )
    eos_reason = fields.Selection(
        [
            ("1", "الاستقالة"),
            ("2", "انتهاء مدة العقد المحدد المدة"),
            (
                "3",
                "بلوغ العامل سن التقاعد وفق ما تقضي به أحكام نظام التأمينات الاجتماعية، مالم تمتد مدة العقد المحدد المدة إلى ما بعد هذه السن",
            ),
            (
                "4",
                "فسخ العقد لأحد الأسباب الواردة في المادتين (75) ، (80) من نظام العمل",
            ),
            ("5", "ترك العامل العمل في الحالات الواردة في المادة (81) من نظام العمل"),
            (
                "6",
                "انقطاع العامل عن العمل بسبب مرضه لمدد تزيد في مجموعها على مئة وعشرين يوماً متقطعة أو متصلة خلال السنة الواحدة التي تبدأ من تاريخ أول إجازة مرضية",
            ),
            (
                "7",
                "عجز العامل عجزاً كلياً عن أداء العمل المتفق عليه، ويثبت ذلك بتقرير طبي معتمد",
            ),
            ("8", "وفاة العامل"),
            (
                "9",
                "إذا ألغت السلطات الحكومية المختصة رخصة عمل أو إقامة العامل غير السعودي أو قررت عدم تجديدها أو إبعاده عن البلاد",
            ),
            ("10", "إغلاق المنشأة نهائياً"),
            ("11", "إنهاء النشاط الذي يعمل فيه العامل، مالم يتفق على غير ذلك"),
            (
                "12",
                "طلب الإحالة إلى التقاعد قبل بلوغ السن النظامية حسب نظام التقاعد وموافقة صاحب الصلاحية على ذلك",
            ),
            (
                "13",
                "عدم الكفاءة لحصوله على تقويم أداء وظيفي بتقدير غير مُرضٍ ثلاث مرات متتالية بشرط ألا تقل مدة التقويم عن ( 18 ) ثمانية عشر شهراً، وأن يصدر في هذه الحالة قرار من صاحب الصلاحية",
            ),
            ("14", "فسخ العقد على المادة (77) من نظام العمل"),
        ],
        string="EOS Reason",
        tracking=True,
        computed="compute_eos_reason",
        store=True,
    )

    @api.depends("employee_eos_reason")
    def compute_eos_reason(self):
        for termination in self:
            termination.eos_reason = termination.eos_reason

    request_type = fields.Selection(
        string="Request Type",
        selection=[
            ("Non-renewal", "Non-renewal"),
            ("Retirement", "Retirement"),
            ("End-Service", "End-Service"),
        ],
        required=False,
    )
    last_work_date = fields.Date(string="Last Work Date", required=False)

    @api.constrains("employee_eos_reason", "employee_id")
    def _constrain_employee_eos_reason(self):
        for rec in self:
            if (
                rec.employee_id.user_id != self.env.user
                and rec.requested_by == "employee"
            ):
                raise exceptions.ValidationError(
                    _("You are not authorized to request for this employee")
                )

    @api.onchange("employee_id")
    def compute_last_work_date(self):
        for termination in self:
            contract_id = termination.employee_id.contract_id
            if contract_id and contract_id.state == "open":
                last_work_date = termination.request_date + relativedelta(days=60)
                if (
                    contract_id.limited_contract
                    and termination.employee_id.contract_id.date_end
                    and last_work_date > termination.employee_id.contract_id.date_end
                ):
                    last_work_date = termination.employee_id.contract_id.date_end
                termination.last_work_date = last_work_date
            else:
                termination.last_work_date = False

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "confirm"
                rec.employee_id.contract_id.write({"sub_state": "termination_process"})

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code(
            "resignation.request"
        ) or _("New")
        return super(resignation_request, self).create(values)
