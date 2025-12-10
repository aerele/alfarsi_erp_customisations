import frappe
from frappe.utils import today, add_months

def update_operations_number_cards():
    docs = ["Payments Collected", "Purchase Outstanding Amount", "Total Purchase Amount", "PDC collection", "Outstanding amount", "Total Sales Invoices"]
    for doc in docs:
        doc = frappe.get_doc("Number Card", doc)
        doc.filters_json = frappe.as_json({
            "from_date": add_months(today(), -1),
            "to_date": today()
        })
        doc.save()
