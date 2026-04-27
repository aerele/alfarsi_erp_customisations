# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Sales Order",
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 140,
		},
		{
			"label": "Customer",
			"fieldname": "customer",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": "Department",
			"fieldname": "department",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": "Salesperson",
			"fieldname": "sales_person",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": "Undelivered Amount",
			"fieldname": "pending_amount",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": "Delivery Date",
			"fieldname": "delivery_date",
			"fieldtype": "Date",
			"width": 130,
		},
	]


def get_data(filters):
	conditions = build_conditions(filters)
	query = f"""
        SELECT
            so.name AS sales_order,
            so.customer,
            COALESCE(item.custom_item_department, 'Not Set') AS department,
            (
                SELECT st.sales_person
                FROM `tabSales Team` st
                WHERE st.parent = so.name
                LIMIT 1
            ) AS sales_person,

            SUM(
                (soi.qty - IFNULL(soi.delivered_qty, 0)) * soi.base_rate
            ) AS pending_amount,

            so.delivery_date
        FROM `tabSales Order` so
        INNER JOIN `tabSales Order Item` soi
            ON soi.parent = so.name
        INNER JOIN `tabItem` item
            ON item.name = soi.item_code
        WHERE
            so.docstatus = 1
            AND so.status NOT IN ('Completed', 'Cancelled')
            # AND IFNULL(so.per_delivered, 0) < 100
            AND (soi.qty - IFNULL(soi.delivered_qty, 0)) > 0
            {conditions}
        GROUP BY
            so.name,
            item.custom_item_department
        ORDER BY
            so.delivery_date ASC
    """
	return frappe.db.sql(query, filters, as_dict=True)


def build_conditions(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += " AND so.delivery_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND so.delivery_date <= %(to_date)s"
	if filters.get("company"):
		conditions += " AND so.company = %(company)s"
	if filters.get("department"):
		conditions += " AND item.custom_item_department = %(department)s"
	if filters.get("sales_person"):
		conditions += """
            AND EXISTS (
                SELECT 1 FROM `tabSales Team` st
                WHERE st.parent = so.name
                AND st.sales_person = %(sales_person)s
            )
        """
	return conditions
