import frappe


def validate(doc,method):
    validate_customer(doc)
    validate_unfreeze_permissions(doc)


def validate_customer(doc):

    user = frappe.session.user
    allowed_roles = ["Chief Mentor", "Finance Manager", "System Manager"]

    roles = frappe.get_roles(user)
    
    if doc.is_new():
        exists = frappe.db.exists(
            "Customer",
            {"customer_name": doc.customer_name}
        )
        if exists:
            frappe.throw(
                f"Customer with name '{doc.customer_name}' already exists."
            )
        if not any(role in allowed_roles for role in roles):
            frappe.throw(
                "You don't have permission to create a customer.",
                frappe.PermissionError
            )

def validate_unfreeze_permissions(doc):
    old = doc.get_doc_before_save()
    if old and old.is_frozen and not doc.is_frozen:
        tolerance_order = frappe.db.sql("""
            SELECT name
            FROM `tabSales Order`
            WHERE customer = %s
            AND (custom_within_tolerance_amount = 1
                 OR custom_within_tolerance_days = 1)
            LIMIT 1
        """, (doc.name,), as_dict=True)
        if tolerance_order:
            allowed_roles = ["Finance Manager", "System Manager", "Chief Mentor"]
            user_roles = frappe.get_roles()
            if not any(role in allowed_roles for role in user_roles):
                frappe.throw(
                    "Customer ID {} has orders within tolerance. Only Finance Manager can unfreeze.".format(doc.name),
                    frappe.PermissionError
                )