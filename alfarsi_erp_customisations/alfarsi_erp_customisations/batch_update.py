import frappe


def update_from_purchase_receipt(doc, method=None):
	for item in doc.get("items"):
		batch_no = frappe.db.get_value("Purchase Receipt Item", item.name, "batch_no")
		if not batch_no:
			continue

		values = {}
		if item.supplier_batch_no:
			values["supplier_batch_no"] = item.supplier_batch_no
		if item.expiry_date:
			values["expiry_date"] = item.expiry_date

		if values:
			frappe.db.set_value("Batch", batch_no, values)
