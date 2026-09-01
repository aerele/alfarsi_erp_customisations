"""Replay migrated salary-loan repayments that were not allocated to Loan Demands."""

import frappe
from lending.loan_management.doctype.loan_repayment_repost.loan_repayment_repost import (
	process_loan_repayment_repost,
)


def execute():
	backfill_missing_value_dates()
	loans = get_affected_loans()
	validate_loan_accrual_frequency(loans)

	for loan in loans:
		repost_date = get_repost_date(loan)
		if not repost_date:
			continue

		repost = get_existing_repost(loan, repost_date)
		if repost:
			if repost.docstatus != 0 or repost.status != "Draft":
				continue
		else:
			repost = frappe.new_doc("Loan Repayment Repost")
			repost.loan = loan
			repost.repost_date = repost_date
			repost.clear_demand_allocation_before_repost = 1
			repost.cancel_future_emi_demands = 1
			repost.cancel_future_accruals_and_demands = 1
			repost.insert(ignore_permissions=True)

		process_loan_repayment_repost(repost.name)
		frappe.db.commit()


def validate_loan_accrual_frequency(loans):
	if not loans:
		return

	companies = frappe.get_all("Loan", filters={"name": ("in", loans)}, pluck="company")
	missing_companies = sorted(
		{
			company
			for company in companies
			if not frappe.db.get_value("Company", company, "loan_accrual_frequency")
		}
	)
	if missing_companies:
		frappe.throw("Loan Accrual Frequency is required for: " + ", ".join(missing_companies))


def backfill_missing_value_dates():
	frappe.db.sql(
		"""
		UPDATE `tabLoan Repayment`
		SET value_date = posting_date
		WHERE docstatus = 1
		  AND value_date IS NULL
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


def get_existing_repost(loan, repost_date):
	repost = frappe.db.get_value(
		"Loan Repayment Repost",
		{
			"loan": loan,
			"repost_date": repost_date,
			"docstatus": ("!=", 2),
		},
	)
	return frappe.get_doc("Loan Repayment Repost", repost) if repost else None
