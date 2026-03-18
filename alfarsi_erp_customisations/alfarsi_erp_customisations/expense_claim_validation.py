import frappe
from frappe import _


def validate_expense_claim_accounts(doc, method):
    settings = frappe.get_single("Expense Claim Settings")

    allowed_accounts = [
        row.account for row in settings.allowed_expense_accounts if row.account
    ]
    if not allowed_accounts:
        frappe.throw(
            _("Please configure Allowed Expense Accounts in Expense Claim Settings")
        )

    for row in doc.expenses:
        account = row.default_account
        if not account:
            frappe.throw(
                _("No account found for Expense Type {0} in row {1}").format(
                    row.expense_type, row.idx
                )
            )
        if account not in allowed_accounts:
            frappe.throw(
                _(
                    "Account {0} used in row {1} is not allowed in Expense Claim Settings"
                ).format(account, row.idx)
            )
