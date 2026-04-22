# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}

	columns = []
	data = []

	if filters.period == "Monthly":
		if filters.based_on == "Department Wise":
			columns = get_department_columns(filters)
			data = get_department_data(filters)
		else:
			columns = get_columns(filters)
			data = get_monthly_data(filters)

	elif filters.period == "Weekly":
		columns = get_weekly_columns(filters)
		data = get_weekly_data(filters)
	elif filters.period == "Yearly":
		columns = get_yearly_columns()
		data = get_yearly_data(filters)
	return columns, data, None, None, None, True


def get_columns(filters):
	columns = [
		{"label": "Label", "fieldname": "label", "fieldtype": "Data", "width": 220},
		{"label": "Sales", "fieldname": "sales", "fieldtype": "Currency", "width": 150},
		{"label": "Cost", "fieldname": "cost", "fieldtype": "Currency", "width": 150},
		{"label": "Margin %", "fieldname": "margin", "fieldtype": "Percent", "width": 120},
		{"label": "Growth %", "fieldname": "growth", "fieldtype": "Percent", "width": 120},
		{"label": "Target", "fieldname": "target", "fieldtype": "Currency", "width": 150},
		{"label": "Target %", "fieldname": "target_percent", "fieldtype": "Percent", "width": 120},
	]
	return columns


def get_yearly_columns():
	columns = [
		{"label": "Year", "fieldname": "year", "fieldtype": "Data", "width": 120},
		{"label": "Sales", "fieldname": "sales", "fieldtype": "Currency", "width": 150},
		{"label": "Cost", "fieldname": "cost", "fieldtype": "Currency", "width": 150},
		{"label": "Margin %", "fieldname": "margin", "fieldtype": "Percent", "width": 120},
		{"label": "Growth %", "fieldname": "growth", "fieldtype": "Percent", "width": 120},
	]
	return columns


def get_yearly_data(filters):
	company = filters.company

	# sales
	sales_data = frappe.db.sql(
		"""
        SELECT
            YEAR(posting_date) AS year,
            SUM(base_net_total) AS sales
        FROM `tabSales Invoice`
        WHERE
            docstatus = 1
            AND company = %s
        GROUP BY YEAR(posting_date)
        ORDER BY YEAR(posting_date)
    """,
		company,
		as_dict=1,
	)

	# cost
	cost_data = frappe.db.sql(
		"""
        SELECT
            YEAR(posting_date) AS year,
            SUM(stock_value_difference) * -1 AS cost
        FROM `tabStock Ledger Entry`
        WHERE
            voucher_type = 'Delivery Note'
            AND company = %s
            AND is_cancelled = 0
            AND actual_qty < 0
        GROUP BY YEAR(posting_date)
    """,
		company,
		as_dict=1,
	)

	# map for cost
	cost_map = {c.year: c.cost for c in cost_data}
	data = []
	prev_sales = 0
	for s in sales_data:
		sales = s.sales or 0
		cost = cost_map.get(s.year, 0)
		margin = 0
		if sales:
			margin = ((sales - cost) / sales) * 100
		growth = 0
		if prev_sales:
			growth = ((sales - prev_sales) / prev_sales) * 100
		prev_sales = sales

		data.append({"year": s.year, "sales": sales, "cost": cost, "margin": margin, "growth": growth})
	return data


def get_weekly_columns(filters):
	columns = [
		{"label": "Period", "fieldname": "label", "fieldtype": "Data", "width": 220},
		{"label": "Sales", "fieldname": "sales", "fieldtype": "Currency", "width": 150},
		{"label": "Cost", "fieldname": "cost", "fieldtype": "Currency", "width": 150},
		{"label": "Margin %", "fieldname": "margin", "fieldtype": "Percent", "width": 120},
	]
	return columns


def get_weekly_sales(year, company):
	return frappe.db.sql(
		"""
        SELECT
            MONTHNAME(posting_date) AS month,
            MONTH(posting_date) AS month_no,
            FLOOR((DAY(posting_date)-1)/7) + 1 AS week_no,
            SUM(base_net_total) AS sales
        FROM `tabSales Invoice`
        WHERE
            docstatus = 1
            AND company = %s
            AND is_return = 0
            AND YEAR(posting_date) = %s
        GROUP BY
            month_no, week_no
        ORDER BY
            month_no, week_no
    """,
		(company, year),
		as_dict=1,
	)


def get_weekly_cost(year, company):
	return frappe.db.sql(
		"""
        SELECT
            MONTHNAME(posting_date) AS month,
            MONTH(posting_date) AS month_no,
            FLOOR((DAY(posting_date)-1)/7) + 1 AS week_no,
            SUM(stock_value_difference) * -1 AS cost
        FROM `tabStock Ledger Entry`
        WHERE
            voucher_type = 'Delivery Note'
            AND company = %s
            AND is_cancelled = 0
            AND actual_qty < 0
            AND YEAR(posting_date) = %s
        GROUP BY
            month_no, week_no
        ORDER BY
            month_no, week_no
    """,
		(company, year),
		as_dict=1,
	)


def get_weekly_data(filters):
	company = filters.company
	year = filters.year

	sales_data = get_weekly_sales(year, company)
	cost_data = get_weekly_cost(year, company)
	sales_map = {(s.month, s.week_no): s.sales for s in sales_data}
	cost_map = {(c.month, c.week_no): c.cost for c in cost_data}
	months = [
		"January",
		"February",
		"March",
		"April",
		"May",
		"June",
		"July",
		"August",
		"September",
		"October",
		"November",
		"December",
	]
	data = []
	prev_sales = 0
	for m in months:
		month_sales = sum(v for (month, w), v in sales_map.items() if month == m)
		month_cost = sum(v for (month, w), v in cost_map.items() if month == m)
		if month_sales or month_cost:
			data.append({"label": m, "sales": month_sales, "cost": month_cost, "indent": 0})
		month_weeks = sorted(
			set([w for (month, w) in sales_map if month == m] + [w for (month, w) in cost_map if month == m])
		)
		for w in month_weeks:
			sales = sales_map.get((m, w), 0)
			cost = cost_map.get((m, w), 0)
			if not (sales or cost):
				continue
			margin = ((sales - cost) / sales) * 100 if sales else 0
			growth = ((sales - prev_sales) / prev_sales) * 100 if prev_sales else 0
			prev_sales = sales
			data.append(
				{
					"label": f"Week {w}",
					"sales": sales,
					"cost": cost,
					"margin": margin,
					"growth": growth,
					"indent": 1,
				}
			)
	return data


def get_monthly_data(filters):
	year = filters.year
	company = filters.company

	sales_data = get_sales_data(year, company)
	cost_data = get_cost_data(year, company)
	target_map = get_monthly_target_map(year)

	data = []
	months = [
		"January",
		"February",
		"March",
		"April",
		"May",
		"June",
		"July",
		"August",
		"September",
		"October",
		"November",
		"December",
	]
	prev_sales = 0
	for m in months:
		sales = next((x.sales for x in sales_data if x.month == m), 0)
		cost = next((x.cost for x in cost_data if x.month == m), 0)
		target = target_map.get(m, 0)
		margin = 0
		growth = 0
		target_percent = 0

		if sales:
			margin = ((sales - cost) / sales) * 100
		if prev_sales:
			growth = ((sales - prev_sales) / prev_sales) * 100
		if target:
			target_percent = (sales / target) * 100
		prev_sales = sales

		data.append(
			{
				"label": m,
				"sales": sales,
				"cost": cost,
				"margin": margin,
				"growth": growth,
				"target": target,
				"target_percent": target_percent,
			}
		)

	total_sales = sum(d.get("sales", 0) for d in data)
	total_cost = sum(d.get("cost", 0) for d in data)
	total_target = sum(d.get("target", 0) for d in data)
	total_margin = 0
	if total_sales:
		total_margin = ((total_sales - total_cost) / total_sales) * 100
	total_target_percent = (total_sales / total_target) * 100 if total_target else 0

	data.append(
		{
			"label": "Total",
			"sales": total_sales,
			"cost": total_cost,
			"margin": total_margin,
			"growth": "",
			"target": total_target,
			"target_percent": total_target_percent,
			"is_total_row": 1,
			# "bold": 1
		}
	)
	return data


def get_monthly_target(year):
	return frappe.db.sql(
		"""
        SELECT
            td.distribution_id,
            td.target_amount
        FROM `tabTarget Detail` td
        WHERE td.fiscal_year = %s
    """,
		year,
		as_dict=1,
	)


def get_distribution(distribution_id):
	return frappe.db.sql(
		"""
        SELECT
            month,
            percentage_allocation
        FROM `tabMonthly Distribution Percentage`
        WHERE parent = %s
    """,
		distribution_id,
		as_dict=1,
	)


def get_monthly_target_map(year):
	targets = frappe.db.sql(
		"""
        SELECT
            td.target_amount,
            td.distribution_id
        FROM `tabTarget Detail` td
        WHERE td.fiscal_year = %s
    """,
		year,
		as_dict=1,
	)

	month_target = {
		"January": 0,
		"February": 0,
		"March": 0,
		"April": 0,
		"May": 0,
		"June": 0,
		"July": 0,
		"August": 0,
		"September": 0,
		"October": 0,
		"November": 0,
		"December": 0,
	}
	for t in targets:
		distribution = frappe.db.sql(
			"""
            SELECT
                month,
                percentage_allocation
            FROM `tabMonthly Distribution Percentage`
            WHERE parent = %s
        """,
			t.distribution_id,
			as_dict=1,
		)

		for d in distribution:
			month_target[d.month] += flt(t.target_amount * d.percentage_allocation / 100, 2)

	return month_target


def get_department_columns(filters):
	columns = [
		{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 120},
		{"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 200},
		{
			"label": "Sales",
			"fieldname": "sales",
			"fieldtype": "Currency",
		},
		{
			"label": "Cost",
			"fieldname": "cost",
			"fieldtype": "Currency",
		},
		{
			"label": "Margin %",
			"fieldname": "margin",
			"fieldtype": "Percent",
		},
	]
	return columns


def get_sales_data(year, company):
	return frappe.db.sql(
		"""
        SELECT
            MONTHNAME(posting_date) AS month,
            MONTH(posting_date) AS month_no,
            SUM(base_net_total) AS sales
        FROM `tabSales Invoice`
        WHERE
            docstatus = 1
            AND is_return = 0
            AND company = %s
            AND YEAR(posting_date) = %s
        GROUP BY MONTH(posting_date)
        ORDER BY month_no
    """,
		(company, year),
		as_dict=1,
	)


def get_cost_data(year, company):
	return frappe.db.sql(
		"""
        SELECT
            MONTHNAME(posting_date) AS month,
            MONTH(posting_date) AS month_no,
            SUM(stock_value_difference) * -1 AS cost
        FROM `tabStock Ledger Entry`
        WHERE
            company = %s
            AND voucher_type = 'Delivery Note'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            AND actual_qty < 0
        GROUP BY MONTH(posting_date)
        ORDER BY month_no
    """,
		(company, year),
		as_dict=1,
	)


def get_department_data(filters):
	company = filters.get("company")
	year = filters.get("year")

	sales_data = frappe.db.sql(
		"""
        SELECT
            MONTH(si.posting_date) AS month_no,
            MONTHNAME(si.posting_date) AS month,
            UPPER(i.custom_item_department) AS department,
            SUM(sii.base_net_amount) AS sales
            # SUM(dni.base_net_amount) AS sales

        FROM `tabSales Invoice` si

        JOIN `tabSales Invoice Item` sii
            ON sii.parent = si.name

        JOIN `tabItem` i
            ON i.name = sii.item_code

        WHERE
            si.docstatus = 1
            AND si.is_return = 0
            AND si.company = %s
            AND YEAR(si.posting_date) = %s
            AND i.custom_item_department IS NOT NULL

        GROUP BY
            month_no, department

        ORDER BY
            month_no, department
    """,
		(company, year),
		as_dict=1,
	)

	cost_data = frappe.db.sql(
		"""
        SELECT
            MONTH(sle.posting_date) AS month_no,
            MONTHNAME(sle.posting_date) AS month,
            UPPER(i.custom_item_department) AS department,
            SUM(sle.stock_value_difference) * -1 AS cost

        FROM `tabStock Ledger Entry` sle

        JOIN `tabItem` i
            ON i.name = sle.item_code

        WHERE
            sle.voucher_type = 'Delivery Note'
            AND sle.company = %s
            AND sle.is_cancelled = 0
            AND sle.actual_qty < 0
            AND YEAR(sle.posting_date) = %s
            AND i.custom_item_department IS NOT NULL

        GROUP BY
            month_no, department

        ORDER BY
            month_no, department
    """,
		(company, year),
		as_dict=1,
	)

	combined = defaultdict(lambda: {"sales": 0, "cost": 0, "month": "", "month_no": 0})
	for s in sales_data:
		key = (s.month_no, s.department)

		combined[key]["sales"] += s.sales or 0
		combined[key]["month"] = s.month
		combined[key]["month_no"] = s.month_no

	for c in cost_data:
		key = (c.month_no, c.department)

		combined[key]["cost"] += c.cost or 0
		combined[key]["month"] = c.month
		combined[key]["month_no"] = c.month_no

	result = []

	for (_, department), values in combined.items():
		sales = values["sales"]
		cost = values["cost"]

		margin = ((sales - cost) / sales) * 100 if sales else 0

		result.append(
			{
				"month": values["month"],
				"department": department,
				"sales": sales,
				"cost": cost,
				"margin": margin,
				"month_no": values["month_no"],
			}
		)

	result.sort(key=lambda x: (x["month_no"], x["department"]))
	for r in result:
		r.pop("month_no", None)

	return result
