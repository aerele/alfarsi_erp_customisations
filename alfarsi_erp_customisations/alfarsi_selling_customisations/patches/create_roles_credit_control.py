import frappe

def execute():
    create_roles()




def create_roles():
    roles = ["Chief Mentor", "Finance Manager"]
    for role in roles:
        if not frappe.db.exists("Role", {"role_name": role}):
            r = frappe.get_doc({
                "doctype": "Role",
                "role_name": role
            })
            r.insert(ignore_permissions=True)
