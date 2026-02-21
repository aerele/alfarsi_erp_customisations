import frappe

def update_docperm(doctype, perm):
    exists = frappe.get_all(
        "Custom DocPerm",
        filters={
            "parent": doctype,
            "role": perm["role"],
            "permlevel": 0
        }
    )

    if exists:
        permission_doc = frappe.get_doc("Custom DocPerm", exists[0]["name"])
    else:
        permission_doc = frappe.get_doc({
            "doctype": "Custom DocPerm",
            "parent": doctype,
            "parenttype": "DocType",
            "parentfield": "permissions",
            "role": perm["role"],
            "permlevel": 0,
        })

    permission_doc.read = perm.get("read", 0)
    permission_doc.write = perm.get("write", 0)
    permission_doc.submit = perm.get("submit", 0)
    permission_doc.cancel = perm.get("cancel", 0)

    permission_doc.save(ignore_permissions=True)
