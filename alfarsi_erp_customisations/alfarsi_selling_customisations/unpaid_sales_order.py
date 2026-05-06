import frappe


def validate(doc, method):
	paid_amount = paid_amount_so(doc.name)
	total_amount = doc.grand_total or 0

	if paid_amount >= total_amount:
		doc.custom_payment_status = "Paid"
	elif paid_amount == 0:
		doc.custom_payment_status = "Unpaid"
	else:
		doc.custom_payment_status = "Partially Paid"


def paid_amount_so(so_name):
	total_paid = 0
	references = frappe.get_all(
		"Payment Entry Reference",
		filters={"reference_doctype": "Sales Order", "reference_name": so_name},
		fields=["allocated_amount", "parent"],
	)
	for ref in references:
		if frappe.db.get_value("Payment Entry", ref.parent, "docstatus") == 1:
			total_paid += ref.allocated_amount or 0
	return total_paid
