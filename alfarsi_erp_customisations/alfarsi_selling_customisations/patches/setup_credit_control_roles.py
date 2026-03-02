import frappe
from alfarsi_erp_customisations.alfarsi_selling_customisations.utils import update_docperm

def execute():
    set_sales_order_permissions(commit=True)
    set_customer_permissions(commit=True)
    set_linked_doctype_permissions(commit=True)


def set_sales_order_permissions(commit=False):
    doctype = "Sales Order"

    permissions = [
        {"role": "Chief Mentor", "read": 1, "write": 1, "submit": 1, "cancel": 0},
        {"role": "Finance Manager", "read": 1, "write": 1, "submit": 1, "cancel": 1},
    ]

    for perm in permissions:
        update_docperm(doctype, perm)
    
    # if commit:
    frappe.db.commit()


def set_customer_permissions(commit=False):
    doctype = "Customer"

    permissions = [
        {"role": "Chief Mentor", "read": 1, "write": 1},
        {"role": "Finance Manager", "read": 1, "write": 1},
    ]

    for perm in permissions:
        update_docperm(doctype, perm)

    # if commit:
    frappe.db.commit()

def set_linked_doctype_permissions(commit=False):
    linked_doctypes = ["Address","Employee", "Contact", "Payment Entry",]
    roles = ["Chief Mentor", "Finance Manager"]

    for doctype in linked_doctypes:
        for role in roles:
            # Default: read/write/create
            perm = {"role": role, "read": 1, "write": 1, "create": 1}
            update_docperm(doctype, perm)

    if commit:
        frappe.db.commit()
    frappe.log_error("Linked DocType permissions updated successfully.")