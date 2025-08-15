import frappe
from frappe.utils import add_days, today

def mark_rejoined(doc, method):
    next_day = add_days(doc.to_date, 1)
    if doc.custom_rejoined and next_day != today():
        new_doc = frappe.new_doc("Leave Application")
        new_doc.employee = doc.employee
        new_doc.leave_type = doc.leave_type
        new_doc.from_date = next_day
        new_doc.to_date = add_days(frappe.utils.today(), -1)
        new_doc.description = f"{doc.description} (Late Rejoin)"
        new_doc.custom_replacement = doc.custom_replacement
        new_doc.custom_rejoined = True
        new_doc.leave_approver = doc.leave_approver
        new_doc.leave_approver_name = doc.leave_approver_name
        new_doc.save()