import frappe
import re
from frappe.utils import nowdate

@frappe.whitelist()
def create_purchase_order(items):

    if isinstance(items, str):
        import json
        items = json.loads(items)

    if not items:
        frappe.throw("No items selected")

    po = frappe.new_doc("Purchase Order")
    po.company = items[0].get("company") or frappe.defaults.get_user_default("Company")
    po.transaction_date = nowdate()
    po.schedule_date = items[0].get("required_by")
    po.supplier = items[0].get("supplier")
    supplier_currency = frappe.db.get_value("Supplier", items[0].get("supplier"), "default_currency")
    if supplier_currency:
        po.currency = supplier_currency

    for row in items:
        item_field = row.get("item_code", "")

        # Extract item_code if HTML link, else plain
        match = re.search(r'>([^<]+)<', item_field)
        if match:
            full_text = match.group(1).strip()
        else:
            full_text = item_field.strip()

        item_code = full_text.split(" - ")[0].strip()

        po.append("items", {
            "item_code": item_code,
            "qty": row.get("total_requirement") or 1,
            "schedule_date": row.get("required_by") or nowdate(),
            "rate": row.get("rate") or 0
        })

    po.set_missing_values()
    po.insert()
    return po.name
