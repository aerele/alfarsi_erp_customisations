import frappe
from frappe import _


def restrict_expense_accounts(doc, method):
    settings = frappe.get_single("Expense Claim Settings")

    restricted_accounts = [
        row.account for row in settings.allowed_expense_accounts if row.account
    ]
    if not restricted_accounts:
        return
    if doc.voucher_type == "Expense Claim":
        return

    if doc.account in restricted_accounts:
        if doc.voucher_type != "Expense Claim":
            frappe.throw(
                _("Account {0} can only be used through Expense Claim").format(
                    doc.account
                )
            )
