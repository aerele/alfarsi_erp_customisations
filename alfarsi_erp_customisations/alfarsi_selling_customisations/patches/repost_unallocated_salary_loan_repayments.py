"""Replay migrated salary-loan repayments that were not allocated to Loan Demands."""

import frappe


def execute():
	backfill_missing_value_dates()

	for loan in get_affected_loans():
		repost_date = get_repost_date(loan)
		if not repost_date or repost_exists(loan, repost_date):
			continue

		repost = frappe.new_doc("Loan Repayment Repost")
		repost.loan = loan
		repost.repost_date = repost_date
		repost.clear_demand_allocation_before_repost = 1
		repost.cancel_future_emi_demands = 1
		repost.cancel_future_accruals_and_demands = 1
		repost.insert(ignore_permissions=True)
		repost.submit()
		frappe.db.commit()


def backfill_missing_value_dates():
	frappe.db.sql(
		"""
		UPDATE `tabLoan Repayment`
		SET value_date = posting_date
		WHERE docstatus = 1
		  AND (value_date IS NULL OR value_date = '')
		"""
	)


def get_affected_loans():
	return frappe.db.sql(
		"""
		SELECT DISTINCT loan.name
		FROM `tabLoan` loan
		INNER JOIN `tabLoan Repayment` repayment
			ON repayment.against_loan = loan.name
			AND repayment.docstatus = 1
			AND repayment.repayment_type = 'Normal Repayment'
		LEFT JOIN `tabLoan Repayment Detail` repayment_detail
			ON repayment_detail.parent = repayment.name
		LEFT JOIN `tabLoan Demand` demand
			ON demand.loan = loan.name
			AND demand.docstatus = 1
			AND demand.outstanding_amount > 0
		WHERE loan.is_term_loan = 1
		  AND loan.repay_from_salary = 1
		  AND loan.total_principal_paid > 0
		  AND demand.name IS NOT NULL
		  AND (repayment_detail.name IS NULL OR IFNULL(repayment_detail.loan_demand, '') = '')
		""",
		pluck=True,
	)


def get_repost_date(loan):
	return frappe.db.sql(
		"""
		SELECT MIN(value_date)
		FROM `tabLoan Repayment`
		WHERE against_loan = %s
		  AND docstatus = 1
		  AND repayment_type = 'Normal Repayment'
		""",
		(loan,),
		pluck=True,
	)[0]


def repost_exists(loan, repost_date):
	return frappe.db.exists(
		"Loan Repayment Repost",
		{
			"loan": loan,
			"repost_date": repost_date,
			"docstatus": ("!=", 2),
		},
	)
