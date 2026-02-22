from odoo import api, fields, models, _
from collections import defaultdict, Counter
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.osv.expression import AND


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    is_overtime_rule = fields.Boolean(string="Is Overtime?")
    allowance_rule = fields.Char(related="category_id.code", readonly=True, store=True)

    @api.onchange("is_overtime_rule")
    def onchange_is_overtime_rule(self):
        if self.is_overtime_rule:
            self.update(
                {
                    "condition_select": "python",
                    "condition_python": "result = payslip.overtime_request_ids",
                    "amount_select": "code",
                    "amount_python_compute": "result = sum(payslip.overtime_request_ids.mapped('total_request_amount'))",
                }
            )


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    overtime_request_ids = fields.Many2many(
        comodel_name="overtime.request",
        relation="payslip_overtime_requests",
        string="Overtime Requests",
    )

    def compute_sheet(self):
        for rec in self:
            rec.overtime_request_ids = (
                self.env["overtime.request"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", rec.employee_id.id),
                        ("state", "=", "confirm"),
                        ("request_date", ">=", rec.date_from),
                        ("request_date", "<=", rec.date_to),
                    ]
                )
            )
        return super(HrPayslip, self).compute_sheet()

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for rec in self:
            rec.overtime_request_ids.action_paid()
        return res

    @api.model
    def _get_dashboard_warnings(self):
        # Retrieve the different warnings to display on the actions section (box on the left)
        result = []

        # Employees section
        employees_default_title = _("Employees")
        # Retrieve employees:
        # - with no open contract, and date_end in the past
        # - with no contract, and not green draft contract
        employees_without_contracts = self.env["hr.employee"]
        all_employees = self.env["hr.employee"].search(
            [
                ("employee_type", "=", "employee"),
                ("company_id", "in", self.env.companies.ids),
            ]
        )
        today = fields.Date.today()
        for employee in all_employees:
            if (
                employee.contract_id
                and employee.contract_id.date_end
                and employee.contract_id.date_end < today
            ):
                employees_without_contracts += employee
            elif not employee.contract_id:
                existing_draft_contract = self.env["hr.contract"].search(
                    [
                        ("employee_id", "=", employee.id),
                        ("company_id", "=", employee.company_id.id),
                        ("state", "=", "draft"),
                        ("kanban_state", "=", "done"),
                    ]
                )
                if not existing_draft_contract:
                    employees_without_contracts += employee
        if employees_without_contracts:
            result.append(
                {
                    "string": _("Employees Without Running Contracts"),
                    "count": len(employees_without_contracts),
                    "action": self._dashboard_default_action(
                        employees_default_title,
                        "hr.employee",
                        employees_without_contracts.ids,
                    ),
                }
            )

        # Retrieve employees whose company on contract is different than employee's company
        employee_with_different_company_on_contract = self.env["hr.employee"]
        contracts = (
            self.sudo()
            .env["hr.contract"]
            .search(
                [
                    ("state", "in", ["draft", "open"]),
                    ("employee_id", "in", all_employees.ids),
                ]
            )
        )

        for contract in contracts:
            if contract.employee_id.company_id != contract.company_id:
                employee_with_different_company_on_contract |= contract.employee_id
        if employee_with_different_company_on_contract:
            result.append(
                {
                    "string": _("Employee whose contracts and company are differents"),
                    "count": len(employee_with_different_company_on_contract),
                    "action": self._dashboard_default_action(
                        employees_default_title,
                        "hr.employee",
                        employee_with_different_company_on_contract.ids,
                    ),
                }
            )

        # Retrieves last batches (this month, or last month)
        batch_limit_date = fields.Date.today() - relativedelta(months=1, day=1)
        batch_group_read = (
            self.env["hr.payslip.run"]
            .with_context(lang="en_US")
            ._read_group(
                [
                    (
                        "date_start",
                        ">=",
                        fields.Date.today() - relativedelta(months=1, day=1),
                    )
                ],
                fields=["date_start"],
                groupby=["date_start:month"],
                orderby="date_start desc",
            )
        )
        # Keep only the last month
        batch_group_read = batch_group_read[:1]
        if batch_group_read:
            if batch_group_read[-1]["__range"].get("date_start:month"):
                min_date = datetime.strptime(
                    batch_group_read[-1]["__range"]["date_start:month"]["from"],
                    "%Y-%m-%d",
                )
            else:
                min_date = batch_limit_date
            last_batches = self.env["hr.payslip.run"].search(
                [("date_start", ">=", min_date)]
            )
        else:
            last_batches = self.env["hr.payslip.run"]

        payslips_with_negative_net = self.env["hr.payslip"]

        employee_payslips = defaultdict(
            lambda: defaultdict(lambda: self.env["hr.payslip"])
        )
        employee_calendar_contracts = defaultdict(
            lambda: defaultdict(lambda: self.env["hr.contract"])
        )
        employee_payslip_contracts = defaultdict(lambda: self.env["hr.contract"])
        for slip in last_batches.slip_ids:
            if slip.state == "cancel":
                continue
            employee = slip.employee_id
            contract = slip.contract_id
            calendar = contract.resource_calendar_id
            struct = slip.struct_id

            employee_payslips[struct][employee] |= slip

            employee_calendar_contracts[employee][calendar] |= contract

            employee_payslip_contracts[employee] |= contract

            if slip.net_wage < 0:
                payslips_with_negative_net |= slip

        employees_previous_contract = self.env["hr.employee"]
        for employee, used_contracts in employee_payslip_contracts.items():
            if employee.contract_id not in used_contracts:
                employees_previous_contract |= employee

        employees_multiple_payslips = self.env["hr.payslip"]
        for dummy, employee_slips in employee_payslips.items():
            for employee, payslips in employee_slips.items():
                if len(payslips) > 1:
                    employees_multiple_payslips |= payslips
        if employees_multiple_payslips:
            multiple_payslips_str = _(
                "Employees With Multiple Open Payslips of Same Type"
            )
            result.append(
                {
                    "string": multiple_payslips_str,
                    "count": len(employees_multiple_payslips.employee_id),
                    "action": self._dashboard_default_action(
                        multiple_payslips_str,
                        "hr.payslip",
                        employees_multiple_payslips.ids,
                        additional_context={"search_default_group_by_employee_id": 1},
                    ),
                }
            )

        employees_missing_payslip = self.env["hr.employee"].search(
            [
                ("company_id", "in", last_batches.company_id.ids),
                ("id", "not in", last_batches.slip_ids.employee_id.ids),
                ("contract_warning", "=", False),
            ]
        )
        if employees_missing_payslip:
            missing_payslips_str = _(
                "Employees (With Running Contracts) missing from open batches"
            )
            result.append(
                {
                    "string": missing_payslips_str,
                    "count": len(employees_missing_payslip),
                    "action": self._dashboard_default_action(
                        missing_payslips_str,
                        "hr.contract",
                        employees_missing_payslip.contract_id.ids,
                    ),
                }
            )

        # Retrieve employees with both draft and running contracts
        ambiguous_domain = [
            ("company_id", "in", self.env.companies.ids),
            ("employee_id", "!=", False),
            "|",
            "&",
            ("state", "=", "draft"),
            ("kanban_state", "!=", "done"),
            ("state", "=", "open"),
        ]
        employee_contract_groups = self.env["hr.contract"]._read_group(
            ambiguous_domain, fields=["state:count_distinct"], groupby=["employee_id"]
        )
        ambiguous_employee_ids = [
            group["employee_id"][0]
            for group in employee_contract_groups
            if group["state"] == 2
        ]
        if ambiguous_employee_ids:
            ambiguous_contracts_str = _("Employees With Both New And Running Contracts")
            ambiguous_contracts = self.env["hr.contract"].search(
                AND([ambiguous_domain, [("employee_id", "in", ambiguous_employee_ids)]])
            )
            result.append(
                {
                    "string": ambiguous_contracts_str,
                    "count": len(ambiguous_employee_ids),
                    "action": self._dashboard_default_action(
                        ambiguous_contracts_str,
                        "hr.contract",
                        ambiguous_contracts.ids,
                        additional_context={"search_default_group_by_employee": 1},
                    ),
                }
            )

        # Work Entries section
        start_month = fields.Date.today().replace(day=1)
        next_month = start_month + relativedelta(months=1)
        work_entries_in_conflict = self.env["hr.work.entry"].search_count(
            [
                ("state", "=", "conflict"),
                ("date_stop", ">=", start_month),
                ("date_start", "<", next_month),
            ]
        )
        if work_entries_in_conflict:
            result.append(
                {
                    "string": _("Conflicts"),
                    "count": work_entries_in_conflict,
                    "action": "hr_work_entry.hr_work_entry_action_conflict",
                }
            )

        multiple_schedule_contracts = self.env["hr.contract"]
        for employee, calendar_contracts in employee_calendar_contracts.items():
            if len(calendar_contracts) > 1:
                for dummy, contracts in calendar_contracts.items():
                    multiple_schedule_contracts |= contracts
        if multiple_schedule_contracts:
            schedule_change_str = _("Working Schedule Changes")
            result.append(
                {
                    "string": schedule_change_str,
                    "count": len(multiple_schedule_contracts.employee_id),
                    "action": self._dashboard_default_action(
                        schedule_change_str,
                        "hr.contract",
                        multiple_schedule_contracts.ids,
                        additional_context={"search_default_group_by_employee": 1},
                    ),
                }
            )

        # Nearly expired contracts
        date_today = fields.Date.from_string(fields.Date.today())
        days = self.env.company.contract_expire_days_num
        # outdated_days = fields.Date.to_string(date_today + relativedelta(days=+14))
        outdated_days = fields.Date.to_string(date_today + relativedelta(days=+days))
        nearly_expired_contracts = self.env[
            "hr.contract"
        ]._get_nearly_expired_contracts(outdated_days)
        if nearly_expired_contracts:
            result.append(
                {
                    "string": _("Running contracts coming to an end"),
                    "count": len(nearly_expired_contracts),
                    "action": self._dashboard_default_action(
                        "Employees with running contracts coming to an end",
                        "hr.contract",
                        nearly_expired_contracts.ids,
                    ),
                }
            )

        # Payslip Section
        if employees_previous_contract:
            result.append(
                {
                    "string": _("Payslips Generated On Previous Contract"),
                    "count": len(employees_previous_contract),
                    "action": self._dashboard_default_action(
                        _("Employees with payslips generated on the previous contract"),
                        "hr.employee",
                        employees_previous_contract.ids,
                    ),
                }
            )
        if payslips_with_negative_net:
            result.append(
                {
                    "string": _("Payslips With Negative Amounts"),
                    "count": len(payslips_with_negative_net),
                    "action": self._dashboard_default_action(
                        _("Payslips with negative NET"),
                        "hr.payslip",
                        payslips_with_negative_net.ids,
                    ),
                }
            )

        # new contracts warning
        new_contracts = self.env["hr.contract"].search(
            [
                ("state", "=", "draft"),
                ("employee_id", "!=", False),
                ("kanban_state", "=", "normal"),
            ]
        )
        if new_contracts:
            new_contracts_str = _("New Contracts")
            result.append(
                {
                    "string": new_contracts_str,
                    "count": len(new_contracts),
                    "action": self._dashboard_default_action(
                        new_contracts_str, "hr.contract", new_contracts.ids
                    ),
                }
            )

        return result
