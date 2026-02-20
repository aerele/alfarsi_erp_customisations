import frappe


def create_custom_fields():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    customer_custom_fields = get_custom_fields("customer_custom_fields.json")
    create_custom_fields(customer_custom_fields)
    sales_order_custom_fields = get_custom_fields("sales_order_custom_fields.json")
    create_custom_fields(sales_order_custom_fields)

# def get_custom_fields():
#     path = frappe.get_app_path("alfarsi_erp_customisations", "alfarsi_selling_customisations", "custom", "customer_custom_fields.json",)
#     custom_fields = frappe.get_file_json(path)
#     return custom_fields

def get_custom_fields(json_file):
    path = frappe.get_app_path("alfarsi_erp_customisations", "alfarsi_selling_customisations", "custom", json_file,)
    custom_fields = frappe.get_file_json(path)
    return custom_fields

# customer_fields = get_custom_fields("customer_custom_fields.json")
# sales_order_fields = get_custom_fields("sales_order_custom_fields.json")
