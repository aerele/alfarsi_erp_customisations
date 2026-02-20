import frappe


def create_custom_fields():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    custom_fields = get_custom_fields()
    create_custom_fields(custom_fields)


def get_custom_fields():
    path = frappe.get_app_path("alfarsi_erp_customisations", "alfarsi_selling_customisations", "custom", "customer_custom_fields.json")
    custom_fields = frappe.get_file_json(path)
    return custom_fields
