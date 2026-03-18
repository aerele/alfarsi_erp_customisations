# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    filters = filters or {}
    for key in ["company", "from_date", "to_date"]:
        if not filters.get(key):
            filters[key] = None

    validate_filters(filters)
    departments = get_used_departments(filters)
    columns = get_columns(departments)
    data = get_data(filters, departments)
    return columns, data


def get_columns(departments):
    columns = [
        {"label": "Name", "fieldname": "name", "fieldtype": "Data", "width": 300}
    ]

    for dept in departments:
        columns.append(
            {
                "label": dept,
                "fieldname": frappe.scrub(dept),
                "fieldtype": "Currency",
                "width": 120,
            }
        )

    columns.append(
        {"label": "Total", "fieldname": "total", "fieldtype": "Currency", "width": 150}
    )

    return columns


def get_data(filters, departments):
    rows = frappe.db.sql(
        """
        SELECT
            ecd.expense_type,
            ecd.custom_expense_claim_sub_categories as sub_type,
            ecd.amount,
            ec.employee,
            emp.employee_name,
            COALESCE(emp.department,'No Department') as department
        FROM `tabExpense Claim Detail` ecd
        JOIN `tabExpense Claim` ec
            ON ec.name = ecd.parent
        LEFT JOIN `tabEmployee` emp
            ON emp.name = ec.employee
        WHERE ec.docstatus = 1
        AND (%(company)s IS NULL OR ec.company = %(company)s)
        AND (%(from_date)s IS NULL OR ec.posting_date >= %(from_date)s)
        AND (%(to_date)s IS NULL OR ec.posting_date <= %(to_date)s)
    """,
        filters,
        as_dict=True,
    )

    return build_tree(rows, departments)


def build_tree(rows, departments):
    grouped = {}

    for row in rows:
        exp_type = row.expense_type or "Unknown"
        sub_type = row.sub_type or "Unknown"
        employee = row.employee_name or row.employee
        dept = row.department or "No Department"
        amt = row.amount or 0

        grouped.setdefault(exp_type, {})
        grouped[exp_type].setdefault(sub_type, {})
        grouped[exp_type][sub_type].setdefault(
            employee, {"amount": 0, "department": dept}
        )

        grouped[exp_type][sub_type][employee]["amount"] += amt

    data = []

    for exp_type, subtypes in grouped.items():
        exp_row = {"name": exp_type, "parent": None, "indent": 0}
        data.append(exp_row)

        for sub_type, employees in subtypes.items():
            sub_row = {"name": sub_type, "parent": exp_type, "indent": 1}
            data.append(sub_row)

            for emp, details in employees.items():
                dept = details["department"]
                amt = details["amount"]

                emp_row = {"name": emp, "parent": sub_type, "indent": 2}

                accumulate(emp_row, dept, amt, departments)
                accumulate(sub_row, dept, amt, departments)
                accumulate(exp_row, dept, amt, departments)

                data.append(emp_row)

    return data


def get_used_departments(filters):
    depts = frappe.db.sql(
        """
		SELECT DISTINCT
            COALESCE(emp.department, 'No Department') as department
        FROM `tabExpense Claim Detail` ecd
        JOIN `tabExpense Claim` ec
            ON ec.name = ecd.parent
        LEFT JOIN `tabEmployee` emp
            ON emp.name = ec.employee
        WHERE ec.docstatus = 1
        AND (%(company)s IS NULL OR ec.company = %(company)s)
        AND (%(from_date)s IS NULL OR ec.posting_date >= %(from_date)s)
        AND (%(to_date)s IS NULL OR ec.posting_date <= %(to_date)s)
    """,
        filters,
        pluck="department",
    )

    departments = []

    for d in depts:
        departments.append(d or "No Department")

    return sorted(set(departments))


def accumulate(row, dept, amount, departments):
    dept = dept or "No Department"

    for d in departments:
        key = frappe.scrub(d)
        if key not in row:
            row[key] = 0

    dept_key = frappe.scrub(dept)

    if dept_key not in row:
        row[dept_key] = 0

    row[dept_key] += amount

    if "total" not in row:
        row["total"] = 0

    row["total"] += amount


def validate_filters(filters):
    if filters.get("from_date") and filters.get("to_date"):
        if filters["from_date"] > filters["to_date"]:
            frappe.throw("From Date cannot be greater than To Date")
