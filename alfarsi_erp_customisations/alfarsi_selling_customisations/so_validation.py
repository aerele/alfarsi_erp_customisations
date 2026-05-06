import frappe


def block_unpaid_website_so(doc, method=None):
	so_list = []

	if doc.doctype == "Delivery Note":
		so_list = [d.against_sales_order for d in doc.items if d.against_sales_order]
	elif doc.doctype == "Sales Invoice":
		so_list = [d.sales_order for d in doc.items if d.sales_order]

	so_list = list(set(so_list))
	if not so_list:
		return

	records = frappe.get_all(
		"Sales Order",
		filters={"name": ["in", so_list], "from_ecommerce": 1, "custom_payment_status": "Unpaid"},
		pluck="name",
	)
	if records:
		frappe.throw(f"{doc.doctype} cannot be created. Unpaid Website Sales Orders: {', '.join(records)}")
