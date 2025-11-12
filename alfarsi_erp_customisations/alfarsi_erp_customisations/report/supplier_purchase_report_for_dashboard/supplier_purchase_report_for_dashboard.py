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
			"label": "Supplier",
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 200,
		},
		{
			"label": "Supplier Name",
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "outstanding_amount",
			"label": "Outstanding amount",
			"fieldtype": "Currency",
			"width": 200,
		},
		{
			"fieldname": "last_paid_amount",
			"label": "Last Paid Amount",
			"fieldtype": "Currency",
			"width": 200,
		},
		{
			"fieldname": "last_paid_date",
			"label": "Last Paid Date",
			"fieldtype": "Date",
			"width": 200,
		},
		{
			"fieldname": "total_purchases",
			"label": "Total Purchases",
			"fieldtype": "Currency",
			"width": 200,
		}
	]

	return columns

def get_data(filters=None):
	condition = ""
	values = {}

	if filters and filters.get("supplier"):
		condition = "AND pi.supplier = %(supplier)s"
		values["supplier"] = filters.get("supplier")
	
	today = date.today()
	from_date = filters.get("from_date") if filters and filters.get("from_date") else (today - timedelta(days=30)).isoformat()
	to_date = filters.get("to_date") if filters and filters.get("to_date") else today.isoformat()
	values["from_date"] = from_date
	values["to_date"] = to_date

	invoices = frappe.db.sql(f"""
        SELECT 
            pi.supplier,
            SUM(IFNULL(pi.outstanding_amount, 0) * IFNULL(pi.conversion_rate, 1)) AS outstanding_amount,
			SUM(pi.base_grand_total) AS total_purchases
        FROM `tabPurchase Invoice` pi
        WHERE pi.docstatus = 1 
            {condition}
            AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY pi.supplier
        HAVING outstanding_amount >= 1
    """, values, as_dict=True)

	suppliers = {
		sp.name: sp.supplier_name 
		for sp in frappe.get_all("Supplier", filters={"disabled": 0} , fields=["name", "supplier_name"])
	}

	data = []
	for inv in invoices:
		last_payment = frappe.get_all(
			"Payment Entry",
			filters={"party_type": "Supplier", "party": inv.supplier, "docstatus": 1},
			fields=["paid_amount", "posting_date"],
			order_by="posting_date desc",
			limit=1
		)
		last_paid_amount = last_payment[0]["paid_amount"] if last_payment else 0
		last_paid_date = last_payment[0]["posting_date"] if last_payment else ""

		data.append({
			"supplier": inv.supplier,
			"supplier_name": suppliers.get(inv.supplier, ""),
			"outstanding_amount": inv.outstanding_amount or 0,
			"last_paid_amount": last_paid_amount,
			"last_paid_date": last_paid_date,
			"total_purchases": inv.total_purchases or 0,
		})

	return data
