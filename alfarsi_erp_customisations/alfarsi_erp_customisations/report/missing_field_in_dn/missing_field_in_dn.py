# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns =[
		{
			"label":"Delivery Note",
			"fieldname":"delivery_note",
			"fieldtype":"Data",
			"width":210
		}
	]

	from_date= filters.get("from_date")
	to_date= filters.get("to_date")
	customer_group=frappe.db.sql('''select name from `tabDelivery Note` where posting_date BETWEEN %s AND %s AND customer_group="Government" and (
                (customer IN ('C01225', 'C01108') 
                AND custom_receipt_voucher IS NULL
				OR custom_sign_and_stamped_dn_copy IS NULL
				)
                OR
                (customer NOT IN ('C01225', 'C01108') 
                AND custom_sign_and_stamped_dn_copy IS NULL) AND status IN ("To Bill", "Completed", "Closed")
            )
			''',as_dict=1,values=(from_date,to_date))
	data=[
		{
			"delivery_note":d.name
		} for d in customer_group

	]
	return columns, data
