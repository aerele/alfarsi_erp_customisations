import frappe
from frappe import _
from frappe.utils import get_url_to_form

def validate_return_delivery_note(doc, method=None):
    if doc.is_return:
        delivery_notes = frappe.get_all("Sales Invoice Item", {"parent": doc.name}, pluck="delivery_note")
        missing_return_dns = []
        for delivery_note in delivery_notes:
            dn_return = frappe.db.get_value(
                "Delivery Note",
                {"return_against": delivery_note, "is_return": 1, "docstatus": 1},
                "name"
            )
            if not dn_return:
                url = get_url_to_form("Delivery Note", delivery_note)
                link = f'<a href="{url}">{delivery_note}</a>'
                if not link in missing_return_dns:
                    missing_return_dns.append(link)
        if missing_return_dns:
            frappe.throw(
                _("The following Delivery Notes have no return Delivery Note:<br>{0}").format("<br>".join(missing_return_dns)),
                title=_("Missing Return Delivery Notes")
            )
        if not doc.custom_return_approved_by_management:
            frappe.throw(_("Sales Invoice Return has not been approved by Management"))