# -*- coding: utf-8 -*-
{
    "name": "Hr Insurance",
    "summary": """ jes HR Insurance""",
    "description": """
        jes HR Insurance
    """,
    "author": "jes",
    "website": "https://www.jes.com/",
    "category": "HR",
    "version": "0.1",
    "depends": ["base", "hr", "oi_hr_salary_schedule","service_update_employee_info"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/sequence.xml",
        "data/cron_task.xml",
        "views/insurance_menu_root.xml",
        "views/categories_insurance.xml",
        "views/company_insurance.xml",
        "views/pricing_insurance.xml",
        "views/policy_insurance.xml",
        "views/add_delete_insurance.xml",
        "views/employee_policy.xml",
        "views/promote_insurance.xml",
        "views/hr_grade_views.xml",
        "views/contract.xml",
        "report/project_report_pdf_view.xml",
        "wizard/report_wizard.xml",
        "report/report_company_insurances_pdf_view.xml",
    ],
}
