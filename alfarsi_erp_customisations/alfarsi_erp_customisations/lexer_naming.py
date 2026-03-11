import frappe
from frappe.model.naming import make_autoname

DOCTYPE_CONFIG = {
    "Purchase Order": ("custom_lexer_doc", "purchase_order_series"),
    "Purchase Receipt": ("custom_lexer_link_pr", "purchase_receipt_series"),
    "Purchase Invoice": ("custom_lexer_link_in_pi", "purchase_invoice_series"),
    "Sales Order": ("custom_lexer_link_in_so", "sales_order_series"),
    "Delivery Note": ("custom_lexer_link_in_dn", "delivery_note_series"),
    "Sales Invoice": ("custom_lexer_in_si", "sales_invoice_series"),
}


def lexer_autoname(doc, method=None):
    if doc.doctype not in DOCTYPE_CONFIG:
        return

    link_field, series_field = DOCTYPE_CONFIG[doc.doctype]
    if not doc.get(link_field):
        return
    try:
        series = frappe.db.get_value(
            "Lexer Import Log", doc.get(link_field), series_field
        )
        if series:
            doc.name = make_autoname(series.strip())

    except Exception as e:
        frappe.log_error(f"Error in lexer_autoname: {str(e)}", "Lexer Autoname Error")
