# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import frappe
from datetime import date, timedelta

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "sales_person",
			"label": "Sales Person",
			"fieldtype": "Data",
			"width": 230,
		},
		{
			"fieldname": "total_sales_invoices",
			"label": "Total Sales Invoices",
			"fieldtype": "Int",
			"width": 230,
		},
		{
			"fieldname": "outstanding_amount",
			"label": "Outstanding amount",
			"fieldtype": "Currency",
			"width": 230,
		},
		{
			"fieldname": "payments_collected",
			"label": "Payments Collected",
			"fieldtype": "Currency",
			"width": 230,
		},
		{
			"fieldname": "pdc_collection",
			"label": "PDC collection",
			"fieldtype": "Currency",
			"width": 230,
		}
	]
	return columns

def get_data(filters):
    sales_persons = frappe.get_all("Sales Person", fields=["name", "employee"])
    data = []

    # If filter has sales_person, filter the list
    if filters and filters.get("sales_person"):
        sales_persons = [sp for sp in sales_persons if sp.name == filters.get("sales_person")]

    today = date.today()
    from_date = filters.get("from_date") if filters and filters.get("from_date") else (today - timedelta(days=30)).isoformat()
    to_date = filters.get("to_date") if filters and filters.get("to_date") else today.isoformat()

    for sp in sales_persons:
        # Total submitted Sales Invoices for this sales person
        total_invoices = frappe.db.sql("""
            SELECT COUNT(DISTINCT si.name)
            FROM `tabSales Invoice` si
            WHERE si.docstatus = 1
            AND si.posting_date BETWEEN %s AND %s
            AND EXISTS (
                SELECT 1 FROM `tabSales Team` st
                WHERE st.parenttype='Sales Invoice'
                AND st.parent=si.name
                AND st.sales_person=%s
            )
        """, (from_date, to_date, sp.name))[0][0] or 0

        outstanding = frappe.db.sql("""
            SELECT SUM(outstanding_amount)
            FROM `tabSales Invoice`
            WHERE docstatus = 1
            AND posting_date BETWEEN %s AND %s
            AND EXISTS (
                SELECT 1 FROM `tabSales Team`
                WHERE parenttype='Sales Invoice' AND parent=`tabSales Invoice`.name AND sales_person=%s
            )
        """, (from_date, to_date, sp.name))[0][0] or 0

        payments_collected = frappe.db.sql("""
            SELECT SUM(paid_amount)
            FROM `tabPayment Entry`
            WHERE docstatus = 1
            AND posting_date BETWEEN %s AND %s
            AND payment_collected_by LIKE %s
        """, (from_date, to_date, f"%{sp.employee}%"))[0][0] or 0

        pdc_collection = frappe.db.sql("""
            SELECT SUM(paid_amount)
            FROM `tabPayment Entry`
            WHERE posting_date BETWEEN %s AND %s
            AND workflow_state='PDC'
            AND payment_collected_by LIKE %s
        """, (from_date, to_date, f"%{sp.employee}%"))[0][0] or 0

        # Only append if at least one value is non-zero
        if any([total_invoices, outstanding, payments_collected, pdc_collection]):
            data.append({
                "sales_person": sp.name,
                "total_sales_invoices": total_invoices,
                "outstanding_amount": outstanding,
                "payments_collected": payments_collected,
                "pdc_collection": pdc_collection
            })

    return data
