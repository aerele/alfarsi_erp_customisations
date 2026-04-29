# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters or {})
	return columns, data


def get_columns():
	cols = [
		{"label": "Party", "fieldname": "party", "fieldtype": "Link", "options": "Customer", "width": 150},
		{"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
		{
			"label": "Account Manager",
			"fieldname": "account_manager",
			"fieldtype": "Link",
			"options": "User",
			"width": 150,
		},
	]

	for y in range(2014, 2027):
		cols.append({"label": str(y), "fieldname": str(y), "fieldtype": "Currency", "width": 120})

	cols.append({"label": "Total", "fieldname": "total", "fieldtype": "Currency", "width": 150})
	return cols


def get_data(filters):
	to_date = filters.get("to_date")
	company = filters.get("company")
	YEAR_START = 2014
	YEAR_END = 2026

	customers = frappe.get_all(
		"Customer",
		filters={"name": ["not in", ["C00001", "C01992", "C02321", "C02097", "C01986"]]},
		fields=["name", "customer_name", "account_manager"],
		order_by="customer_name asc",
	)

	conditions = ["docstatus = 1"]
	if company:
		conditions.append("company = %(company)s")
	if to_date:
		conditions.append("posting_date <= %(to_date)s")

	invoices = frappe.db.sql(
		f"""
        SELECT name, customer, posting_date, base_grand_total, outstanding_amount
        FROM `tabSales Invoice`
        WHERE {" AND ".join(conditions)}
    """,
		{"company": company, "to_date": to_date},
		as_dict=True,
	)

	inv_map = defaultdict(list)
	for inv in invoices:
		inv_map[inv.customer].append(inv)

	pay_map = {}
	if to_date:
		payments = frappe.db.sql(
			"""
            SELECT per.reference_name, SUM(per.allocated_amount) as amt
            FROM `tabPayment Entry Reference` per
            JOIN `tabPayment Entry` pe ON pe.name = per.parent
            WHERE pe.docstatus = 1 AND pe.posting_date <= %s
            GROUP BY per.reference_name
        """,
			to_date,
			as_dict=True,
		)

		for p in payments:
			pay_map[p.reference_name] = p.amt

	data = []
	for c in customers:
		row = {
			"party": c.name,
			"customer_name": c.customer_name,
			"account_manager": c.account_manager,
			"total": 0,
		}
		year_map = defaultdict(float)
		for inv in inv_map.get(c.name, []):
			year = inv.posting_date.year
			if YEAR_START <= year <= YEAR_END:
				if to_date:
					outstanding = inv.base_grand_total - pay_map.get(inv.name, 0)
				else:
					outstanding = inv.outstanding_amount
				year_map[year] += outstanding
				row["total"] += outstanding

		for y in range(YEAR_START, YEAR_END + 1):
			row[str(y)] = year_map.get(y, 0)
		data.append(row)

	total_row = {"party": "Total", "customer_name": "", "account_manager": "", "total": 0}
	for y in range(YEAR_START, YEAR_END + 1):
		total_row[str(y)] = 0
	for row in data:
		for y in range(YEAR_START, YEAR_END + 1):
			total_row[str(y)] += row.get(str(y), 0)
		total_row["total"] += row.get("total", 0)
	data.append(total_row)

	return data
