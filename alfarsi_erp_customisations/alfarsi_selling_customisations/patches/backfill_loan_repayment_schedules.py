"""Backfill v14 Loan child schedules into v16 Lending schedules."""

import frappe

STATUS_MAP = {
	"Draft": "Draft",
	"Sanctioned": "Initiated",
	"Partially Disbursed": "Active",
	"Disbursed": "Active",
	"Active": "Active",
	"Loan Closure Requested": "Active",
	"Closed": "Closed",
	"Written Off": "Closed",
	"Settled": "Closed",
	"Cancelled": "Cancelled",
	"Rejected": "Rejected",
}
STRIP_FIELDS = {
	"name",
	"parent",
	"parentfield",
	"parenttype",
	"idx",
	"creation",
	"modified",
	"modified_by",
	"owner",
	"docstatus",
}


def execute():
	"""Create one submitted schedule for every legacy Loan child schedule."""
	frappe.reload_doc("loan_management", "doctype", "loan_repayment_schedule")
	if not frappe.db.table_exists("Repayment Schedule"):
		frappe.throw(
			"Legacy Repayment Schedule table does not exist. Cannot backfill loan repayment schedules."
		)

	valid_fields = set(frappe.get_meta("Repayment Schedule").get_valid_fields())
	loan_names = frappe.get_all("Loan", filters={"is_term_loan": 1}, pluck="name")
	for index, loan_name in enumerate(loan_names, start=1):
		if frappe.db.exists("Loan Repayment Schedule", {"loan": loan_name, "docstatus": ["!=", 2]}):
			continue
		rows = get_legacy_rows(loan_name, valid_fields)
		if not rows or not any(row.get("payment_date") for row in rows):
			continue

		loan = frappe.get_doc("Loan", loan_name)
		schedule = frappe.new_doc("Loan Repayment Schedule")
		schedule.flags.ignore_validate = True
		if loan.docstatus == 2:
			schedule.flags.ignore_links = True
		schedule.loan = loan.name
		schedule.company = loan.company
		schedule.loan_product = loan.get("loan_product")
		schedule.loan_amount = loan.get("loan_amount")
		schedule.monthly_repayment_amount = loan.get("monthly_repayment_amount")
		schedule.posting_date = loan.get("posting_date")
		schedule.status = "Cancelled" if loan.docstatus == 2 else STATUS_MAP.get(loan.status, "Active")
		schedule.set("repayment_schedule", rows)
		schedule.maturity_date = max(row["payment_date"] for row in rows if row.get("payment_date"))
		schedule.submit()
		if index % 100 == 0:
			frappe.db.commit()

	frappe.db.commit()


def get_legacy_rows(loan_name, valid_fields):
	legacy_rows = frappe.db.sql(
		"""SELECT * FROM `tabRepayment Schedule`
		WHERE parent = %s AND parenttype = 'Loan' ORDER BY idx""",
		loan_name,
		as_dict=True,
	)
	rows = []
	for legacy_row in legacy_rows:
		row = {}
		for fieldname, value in legacy_row.items():
			fieldname = "demand_generated" if fieldname == "is_accrued" else fieldname
			if fieldname in valid_fields and fieldname not in STRIP_FIELDS and value is not None:
				row[fieldname] = value
		if row:
			rows.append(row)
	return rows
