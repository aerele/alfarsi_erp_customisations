import frappe


def validate(doc, method):
	validate_customer(doc)
	validate_unfreeze_permissions(doc)


def validate_customer(doc):
	if doc.is_new():
		exists = frappe.db.exists("Customer", {"customer_name": doc.customer_name})
		if exists:
			frappe.throw(f"Customer with name '{doc.customer_name}' already exists.")


def validate_unfreeze_permissions(doc):
	old = doc.get_doc_before_save()
	if old and old.is_frozen and not doc.is_frozen:
		tolerance_order = frappe.db.sql(
			"""
            SELECT name
            FROM `tabSales Order`
            WHERE customer = %s
            AND (custom_within_tolerance_amount = 1
                 OR custom_within_tolerance_days = 1)
            LIMIT 1
        """,
			(doc.name,),
			as_dict=True,
		)
		if tolerance_order:
			allowed_roles = ["Finance Manager", "System Manager", "Chief Mentor"]
			user_roles = frappe.get_roles()
			if not any(role in allowed_roles for role in user_roles):
				frappe.throw(
					f"Customer ID {doc.name} has orders within tolerance. Only Finance Manager and Chief Mentor can unfreeze.",
					frappe.PermissionError,
				)
