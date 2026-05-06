import frappe


def update_so_payment_status(doc, method=None):
	so_names = set()
	for ref in doc.references or []:
		if ref.reference_doctype == "Sales Order" and ref.reference_name:
			so_names.add(ref.reference_name)
	if not so_names:
		return

	so_data = frappe.get_all(
		"Sales Order",
		filters={"name": ["in", list(so_names)]},
		fields=["name", "grand_total", "custom_payment_status"],
	)
	so_map = {d.name: d for d in so_data}

	for so_name in so_names:
		so = so_map.get(so_name)
		if so:
			update_single_so(so)


def update_single_so(so):
	so_name = so.name
	paid_amount = paid_amount_so(so_name)
	total_amount = so.grand_total or 0

	if paid_amount >= total_amount:
		status = "Paid"
	elif paid_amount == 0:
		status = "Unpaid"
	else:
		status = "Partially Paid"
	if so.custom_payment_status != status:
		frappe.db.set_value("Sales Order", so_name, "custom_payment_status", status)


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
