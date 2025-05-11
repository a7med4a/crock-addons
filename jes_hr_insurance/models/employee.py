from odoo import api, fields, models
from datetime import datetime



class Employee(models.Model):
    _inherit = "hr.employee"



    def get_emp_medical_insurance(self):
        result = {}
        for rec in self:
            # Define the fields to check in priority order
            insurance_sources = [
                rec.last_medical_insurance_id,
                rec.contract_id.medical_insurance_id if rec.contract_id else False,
                rec.grade_id.medical_insurance_id if rec.grade_id else False,
                rec.grade_id.category_id.medical_insurance_id if rec.grade_id.category_id else False,
            ]
            # Get the first non-empty insurance ID
            insurance = next((source for source in insurance_sources if source), False)
            result[rec.id] = insurance
        return result if len(self) > 1 else result.get(self.id, False)




    dependent_ids = fields.Many2many(comodel_name="hr.family")
    policy_id = fields.Many2one(
        comodel_name="insurance.policy",
        string="Policy Number",
        groups="hr.group_hr_user",
    )
    policy_number = fields.Char(string="Policy Number",related="policy_id.policy_number", store=True, )

    has_insurance = fields.Boolean(
        "Has Insurance", copy=False, groups="hr.group_hr_user"
    )
    last_add_insurance = fields.Date(
        "Last Add Insurance Date", groups="hr.group_hr_user"
    )
    last_delete_insurance = fields.Date(
        "Last Delete Insurance Date", groups="hr.group_hr_user"
    )
    last_medical_insurance_id = fields.Many2one(
        "insurance.categ", groups="hr.group_hr_user"
    )
    employee_insurance_cost = fields.Float(
        string="Employee Cost",
        required=False,
        compute="_compute_employee_insurance_cost",
    )
    dependent_insurance_cost = fields.Float(string="Dependent Cost", required=False)
    insurance_cost = fields.Float(string="Total Insurance Cost", required=False)

    grade_id = fields.Many2one(related='contract_id.grade_id',store=True)

    def _compute_employee_insurance_cost(self):
        for employee in self:
            # get all insurances for employee and his dependants
            employee_insurances = self.env["insurance.add.delete"].search(
                [
                    ("emp_id", "=", employee.id),
                    ("insurance_policy", "=", employee.policy_id.id),
                ],
                order="id desc",
            )

            # get all insurance categories for specific employee
            categories = (
                self.env["insurance.add.delete"]
                .search(
                    [
                        ("emp_id", "=", employee.id),
                        ("insurance_policy", "=", employee.policy_id.id),
                    ],
                    order="id desc",
                )
                .mapped("medical_insurance_id.name")
            )

            # get dependants insurances and permenantly deleted insurances
            dependants_insurances = self.env["insurance.add.delete"].search(
                [
                    ("emp_id", "=", employee.id),
                    ("insurance_policy", "=", employee.policy_id.id),
                    ("is_dependent", "=", True),
                ],
                order="id desc",
            )

            data = {}
            stages = []
            total = 0.0
            is_last_category = False
            for index, category in enumerate(categories):
                is_last_category = True if index == 0 else False
                insurances = employee.filter_insurances(
                    employee_insurances, category, True, is_last_category
                )
                stages.append(
                    {
                        "category": category,
                        "name": employee.name,
                        "insurances": [insurances[-1]] if len(insurances) > 0 else [],
                        # take the first date only as he is added with his dependants again
                        "dependants": employee.filter_insurances(
                            dependants_insurances, category, False, is_last_category
                        ),
                    }
                )
            data["stages"], total = employee.get_insurance_cost(stages)
            data["total"] = total
            employee_cost = 0
            dependants_cost_lst = {}
            for stage in data["stages"]:
                for emp in stage.get("insurances"):
                    employee_cost += emp.get("cost")
                    for dependant in stage.get("dependants"):
                        if dependant.get("id", 0) not in dependants_cost_lst:
                            dependants_cost_lst[dependant["id"]] = dependant["cost"]
                        else:
                            dependants_cost_lst[dependant["id"]] += dependant["cost"]
            employee.employee_insurance_cost = employee_cost
            for dep in employee.family_ids:
                if dep.id in dependants_cost_lst:
                    dep.insurance_cost = dependants_cost_lst[dep.id]
                else:
                    dep.insurance_cost = 0.0
            employee.dependent_insurance_cost = sum(
                employee.family_ids.mapped("insurance_cost")
            )
            employee.insurance_cost = (
                employee.dependent_insurance_cost + employee.employee_insurance_cost
            )

    def get_insurance_values(self, insurance):
        self.employee = insurance.emp_id
        cost = self.print_employee_report()["total"]
        return {
            "name": insurance.emp_id.name,
            "gender": insurance.emp_id.gender,
            "start_date": self.env["insurance.add.delete"]
            .search(
                [
                    ("emp_id", "=", insurance.emp_id.id),
                    ("insurance_policy", "=", self.insurance_policy.id),
                ],
                order="id asc",
                limit=1,
            )
            .request_date,
            "end_date": insurance.request_date
            if insurance.request_type == "delete"
            else "Present",
            "cost": cost,
            "type": insurance.request_type,
        }

    def filter_insurances(
        self, insurances, category, parent=False, is_last_category=False
    ):
        # get insurances by category
        insurances = insurances.filtered(
            lambda r: r.medical_insurance_id.name == category
        )
        data = []
        deleted_insurance = None
        termination_date = None
        total_cost = 0.0
        # if employee
        if parent:
            for index, insurance in enumerate(insurances):
                end_date = (
                    deleted_insurance.request_date if deleted_insurance else "Present"
                )
                if insurance.request_type == "delete" and is_last_category:
                    # check with sherif if earliest insurance date or first entry
                    return [
                        {
                            "name": self.name,
                            "gender": self.gender,
                            "start_date": insurances[len(insurances) - 1].request_date,
                            "end_date": insurance.request_date,
                            "type": insurance.request_type,
                        }
                    ]
                # promoted insurance
                elif insurance.request_type == "delete":
                    deleted_insurance = insurance

                else:
                    if insurance.request_type == "add":
                        data.append(
                            {
                                "name": self.name,
                                "gender": self.gender,
                                "start_date": insurances[
                                    len(insurances) - 1
                                ].request_date,
                                "end_date": deleted_insurance.request_date
                                if deleted_insurance
                                else "Present",
                                "type": insurance.request_type,
                            }
                        )
                        # if dependant
        else:
            for index, insurance in enumerate(insurances):
                # deleted insurance
                if insurance.request_type == "delete" and is_last_category:
                    termination_date = insurance.request_date
                    for insurance in insurances:
                        if insurance.request_type == "add" and insurance.family_ids:
                            for i in range(len(insurance.family_ids)):
                                data.append(
                                    {
                                        "id": insurance.family_ids.mapped("id")[i],
                                        "name": insurance.family_ids.mapped(
                                            "name"
                                        )[i],
                                        "relation": insurance.family_ids.mapped(
                                            "relation"
                                        )[i],
                                        "start_date": insurance.request_date,
                                        "end_date": termination_date,
                                        "type": insurance.request_type,
                                    }
                                )
                # promoted insurance
                elif insurance.request_type == "delete":
                    deleted_insurance = insurance
                # other addition in deleted promotion (skip)
                elif insurance.request_type == "add" and is_last_category and index > 0:
                    continue
                    # added dependants
                else:
                    end_date = (
                        deleted_insurance.request_date
                        if deleted_insurance
                        else "Present"
                    )
                    for insurance in insurances:
                        if insurance.request_type == "add" and insurance.family_ids:
                            for i in range(len(insurance.family_ids)):
                                data.append(
                                    {
                                        "id": insurance.family_ids.mapped("id")[i],
                                        "name": insurance.family_ids.mapped(
                                            "name"
                                        )[i],
                                        "relation": insurance.family_ids.mapped(
                                            "relation"
                                        )[i],
                                        "start_date": insurance.request_date,
                                        "end_date": end_date,
                                        "type": insurance.request_type,
                                    }
                                )
        return data

    def get_insurance_cost(self, categories, include_dependants=True):
        # son, daughter, husband, wife, father, mother
        category_total = 0.0
        total = 0.0
        cost = 0.0
        for category in categories:
            category_total = 0.0
            category_id = self.env["insurance.categ"].search(
                [("name", "=", category["category"])], limit=1
            )

            pricing = self.env["insurance.pricing"].search(
                [("insurance_categ_id", "=", category_id.id)], limit=1
            )

            # employee cost
            gender = (
                category["insurances"][0]["gender"]
                if category["insurances"][0]["gender"]
                else "male"
            )
            employee_cost = (
                pricing.male_categ_cost
                if gender == "male"
                else pricing.female_categ_cost
            )
            employee_end_date = (
                category["insurances"][0]["end_date"]
                if category["insurances"][0]["end_date"] != "Present"
                else datetime.now().date()
            )
            category["insurances"][0]["cost"] = round(
                employee_cost
                * (employee_end_date - category["insurances"][0]["start_date"]).days
                / 365,
                2,
            )

            if include_dependants:
                # dependants cost
                for dependant in category["dependants"]:
                    if dependant["relation"] == "son":
                        cost = pricing.male_cost
                    if dependant["relation"] == "daughter":
                        cost = pricing.female_cost
                    if dependant["relation"] == "father":
                        cost = pricing.father_cost
                    if dependant["relation"] == "mother":
                        cost = pricing.mother_cost

                    end_date = (
                        dependant["end_date"]
                        if dependant["end_date"] != "Present"
                        else datetime.now().date()
                    )
                    dependant["cost"] = round(
                        cost * (end_date - dependant["start_date"]).days / 365, 2
                    )
                    category_total += dependant["cost"]

            category_total += category["insurances"][0]["cost"]
            category["category_cost"] = category_total

            total += category_total

        return categories, total
