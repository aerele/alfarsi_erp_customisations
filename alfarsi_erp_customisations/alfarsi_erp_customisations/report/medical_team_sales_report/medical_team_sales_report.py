# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


@frappe.whitelist()
def get_medical_sales_person_options():
	return frappe.get_all(
		"Sales Person",
		filters={
			"department": "Medical Department - AFMS",
			"is_group": 0,
			"enabled": 1,
		},
		pluck="name",
		order_by="name asc",
	)


def get_columns(filters):
	based_on = filters.get("based_on")

	if based_on == "Item Department wise":
		return [
			{"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 300},
			{"label": "Sales Amount", "fieldname": "sales_amount", "fieldtype": "Currency", "width": 150},
		]

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

	if based_on == "Item Department wise":
		return get_item_department_data(filters)

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
		{**filters},
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
            AND EXISTS (
                SELECT 1
                FROM `tabSales Team` st2
                JOIN `tabSales Person` sp2 ON sp2.name = st2.sales_person
                WHERE st2.parent = si.name
                  AND sp2.department = 'Medical Department - AFMS'
            )
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


def get_item_department_data(filters):
	rows = frappe.db.sql(
		"""
        SELECT
            i.custom_item_department AS item_department,
            sp.name AS sales_person,
            ROUND(SUM(
                sii.base_net_amount * (st.allocated_percentage / 100.0)
            ), 3) AS sales_amount,
            ROUND(SUM(
                CASE WHEN si.customer = 'C02279'
                THEN sii.base_net_amount * (st.allocated_percentage / 100.0)
                ELSE 0 END
            ), 3) AS customer_c02279_amount,
            MAX(CASE WHEN si.customer = 'C02279' THEN c.customer_name END) AS customer_c02279_name
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Invoice Item` sii ON sii.parent = si.name
        JOIN
            `tabItem` i ON i.name = sii.item_code
        JOIN
            `tabCustomer` c ON c.name = si.customer
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
            i.custom_item_department, sp.name
        ORDER BY
            sp.name, i.custom_item_department
    """,
		filters,
		as_dict=True,
	)

	department_label = {
		"Medical Laboratory IVD": "Medical Laboratory IVD",
		"Pharma": "Pharmacy",
		"Medicine": "Pharmacy",
		"Special Import": "Special Import",
	}
	department_order = ["Medical Laboratory IVD", "Pharmacy", "Special Import", "Other Groups"]

	grouped = {}
	for row in rows:
		label = department_label.get(row.item_department, "Other Groups")
		person = grouped.setdefault(row.sales_person, {})
		department = person.setdefault(
			label,
			{"sales_amount": 0.0, "customer_c02279_amount": 0.0, "customer_c02279_name": None},
		)
		department["sales_amount"] += row.sales_amount
		department["customer_c02279_amount"] += row.customer_c02279_amount
		if row.customer_c02279_name:
			department["customer_c02279_name"] = row.customer_c02279_name

	tree = []
	for sales_person, departments in grouped.items():
		tree.append(
			{
				"category": sales_person,
				"sales_amount": round(sum(row["sales_amount"] for row in departments.values()), 3),
				"indent": 0,
			}
		)
		for label in department_order:
			if label not in departments:
				continue
			department = departments[label]
			tree.append(
				{
					"category": label,
					"sales_amount": round(department["sales_amount"], 3),
					"indent": 1,
					"parent": sales_person,
				}
			)
			if department["customer_c02279_amount"]:
				customer_name = department["customer_c02279_name"] or "C02279"
				tree.append(
					{
						"category": f"C02279 - {customer_name}",
						"sales_amount": round(department["customer_c02279_amount"], 3),
						"indent": 2,
						"parent": label,
					}
				)

	return tree
