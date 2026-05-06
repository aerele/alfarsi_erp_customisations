# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_columns(filters):
	based_on = filters.get("based_on")

	if based_on == "Sales Person wise":
		return [
			{"label": "Sales Person", "fieldname": "sales_person", "fieldtype": "Data", "width": 200},
			{"label": "Total Sales", "fieldname": "total", "fieldtype": "Currency", "width": 150},
		]

	elif based_on == "Brand wise Total":
		return [
			{"label": "Brand", "fieldname": "brand", "fieldtype": "Data", "width": 200},
			{"label": "Total Sales", "fieldname": "total", "fieldtype": "Currency", "width": 150},
		]

	elif based_on == "Brand wise":
		return [
			{"label": "Brand", "fieldname": "brand", "fieldtype": "Data", "width": 200},
			{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 150},
			{"label": "Total", "fieldname": "total", "fieldtype": "Currency", "width": 150},
		]

	else:
		return [
			{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 250},
			{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 150},
			{"label": "Total", "fieldname": "total", "fieldtype": "Float", "width": 120},
		]


def get_data(filters):
	based_on = filters.get("based_on")

	if based_on == "Sales Person wise":
		return get_sales_person_data(filters)

	elif based_on == "Brand wise Total":
		return get_brand_total_data(filters)

	elif based_on == "Brand wise":
		return get_brand_data(filters)

	else:
		return get_customer_data(filters)


def get_customer_data(filters):
	return frappe.db.sql(
		"""
        SELECT
            CONCAT(c.name, ' - ', c.customer_name) AS customer,
            MONTHNAME(si.posting_date) AS month,
            ROUND(SUM(st.allocated_amount), 3) AS total
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Team` st ON st.parent = si.name
        JOIN
            `tabSales Person` sp ON sp.name = st.sales_person
        JOIN
            `tabCustomer` c ON c.name = si.customer
        WHERE
            si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND (%(sales_person)s IS NULL OR sp.name = %(sales_person)s)
            AND (%(company)s IS NULL OR si.company = %(company)s)
        GROUP BY
            c.name,
            c.customer_name,
            YEAR(si.posting_date),
            MONTH(si.posting_date)
        ORDER BY
            c.name,
            YEAR(si.posting_date),
            MONTH(si.posting_date)
    """,
		filters,
		as_dict=True,
	)


def get_sales_person_data(filters):
	return frappe.db.sql(
		"""
        SELECT
            sp.name AS sales_person,
            ROUND(SUM(st.allocated_amount), 3) AS total
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Team` st ON st.parent = si.name
        JOIN
            `tabSales Person` sp ON sp.name = st.sales_person
        WHERE
            si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND (%(company)s IS NULL OR si.company = %(company)s)
            AND sp.department = 'Medical Department - AFMS'
        GROUP BY
            sp.name
        ORDER BY
            sp.name
    """,
		filters,
		as_dict=True,
	)


def get_brand_total_data(filters):
	return frappe.db.sql(
		"""
        SELECT
            sii.brand AS brand,
            ROUND(SUM(sii.base_net_amount), 3) AS total
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE
            si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND (%(company)s IS NULL OR si.company = %(company)s)
        GROUP BY
            sii.brand
        ORDER BY
            sii.brand
    """,
		filters,
		as_dict=True,
	)


def get_brand_data(filters):
	return frappe.db.sql(
		"""
        SELECT
            sii.brand AS brand,
            MONTHNAME(si.posting_date) AS month,
            ROUND(SUM(
                (st.allocated_amount / si.base_net_total) * sii.base_net_amount
            ), 3) AS total
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Invoice Item` sii ON sii.parent = si.name
        JOIN
            `tabSales Team` st ON st.parent = si.name
        JOIN
            `tabSales Person` sp ON sp.name = st.sales_person
        WHERE
            si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND (%(company)s IS NULL OR si.company = %(company)s)
            AND (%(sales_person)s IS NULL OR sp.name = %(sales_person)s)
        GROUP BY
            sii.brand,
            YEAR(si.posting_date),
            MONTH(si.posting_date)
        ORDER BY
            sii.brand,
            YEAR(si.posting_date),
            MONTH(si.posting_date)
    """,
		filters,
		as_dict=True,
	)
