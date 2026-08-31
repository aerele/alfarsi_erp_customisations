"""Recover Loan Product master data from legacy Loan Type rows."""

import frappe

PRODUCT_FIELDS = (
	"company",
	"maximum_loan_amount",
	"rate_of_interest",
	"penalty_interest_rate",
	"grace_period_in_days",
	"write_off_amount",
	"is_term_loan",
	"disabled",
	"description",
	"payment_account",
	"loan_account",
	"interest_income_account",
	"penalty_income_account",
	"disbursement_account",
	"repayment_schedule_type",
	"repayment_date_on",
)

RELATED_DOCTYPES = (
	"Loan",
	"Loan Application",
	"Loan Disbursement",
	"Loan Demand",
	"Loan Interest Accrual",
	"Loan Repayment",
	"Loan Repayment Schedule",
	"Loan Restructure",
	"Process Loan Classification",
	"Process Loan Interest Accrual",
)


def execute():
	if not frappe.db.table_exists("Loan Type"):
		frappe.throw("Legacy Loan Type table does not exist. Cannot backfill Loan Product data.")

	legacy_products = frappe.db.sql("SELECT * FROM `tabLoan Type` ORDER BY name", as_dict=True)
	if not legacy_products:
		frappe.throw("Legacy Loan Type table is empty. Cannot backfill Loan Product data.")

	product_fields = set(frappe.get_meta("Loan Product").get_valid_fields())
	for legacy_product in legacy_products:
		create_loan_product(legacy_product, product_fields)

	for doctype in RELATED_DOCTYPES:
		backfill_loan_product_link(doctype)
		backfill_loan_product_from_loan(doctype)

	backfill_schedule_loan_product_link()
	backfill_loan_repayment_frequency()
	backfill_loan_demand_schedule_link()
	backfill_repayment_schedule_demand_status()

	frappe.db.commit()


def create_loan_product(legacy_product, product_fields):
	if frappe.db.exists("Loan Product", legacy_product.name):
		return

	product = frappe.new_doc("Loan Product")
	product.flags.ignore_validate = True
	product.product_code = legacy_product.name
	product.product_name = legacy_product.loan_name or legacy_product.name
	for fieldname in PRODUCT_FIELDS:
		if fieldname in product_fields and legacy_product.get(fieldname) is not None:
			product.set(fieldname, legacy_product.get(fieldname))
	product.insert(ignore_permissions=True)


def backfill_schedule_loan_product_link():
	frappe.db.sql(
		"""
        UPDATE `tabLoan Repayment Schedule` schedule
        INNER JOIN `tabLoan` loan ON loan.name = schedule.loan
        SET schedule.loan_product = loan.loan_product
        WHERE (schedule.loan_product IS NULL OR LENGTH(schedule.loan_product) = 0)
          AND loan.loan_product IS NOT NULL
          AND LENGTH(loan.loan_product) > 0
        """
	)


def backfill_loan_product_link(doctype):
	if not frappe.db.table_exists(doctype):
		return

	columns = frappe.db.get_table_columns(doctype)
	if "loan_type" not in columns or "loan_product" not in columns:
		return

	frappe.db.sql(
		f"""
		UPDATE `tab{doctype}` document
		INNER JOIN `tabLoan Product` product ON product.name = document.loan_type
		SET document.loan_product = product.name
		WHERE IFNULL(document.loan_product, '') = ''
		  AND IFNULL(document.loan_type, '') != ''
		"""
	)


def backfill_loan_product_from_loan(doctype):
	if not frappe.db.table_exists(doctype):
		return

	columns = frappe.db.get_table_columns(doctype)
	loan_field = "loan" if "loan" in columns else "against_loan"
	if loan_field not in columns or "loan_product" not in columns:
		return

	frappe.db.sql(
		f"""
		UPDATE `tab{doctype}` document
		INNER JOIN `tabLoan` loan ON loan.name = document.{loan_field}
		SET document.loan_product = loan.loan_product
		WHERE IFNULL(document.loan_product, "") = ""
		  AND IFNULL(loan.loan_product, "") != ""
		"""
	)


def backfill_loan_demand_schedule_link():
	if not frappe.db.table_exists("Loan Demand"):
		return

	frappe.db.sql(
		"""
		UPDATE `tabLoan Demand` demand
		INNER JOIN `tabRepayment Schedule` schedule_detail
			ON schedule_detail.name = demand.repayment_schedule_detail
			AND schedule_detail.parenttype = "Loan Repayment Schedule"
		SET demand.loan_repayment_schedule = schedule_detail.parent
		WHERE IFNULL(demand.loan_repayment_schedule, "") = ""
		"""
	)

	frappe.db.sql(
		"""
		UPDATE `tabLoan Demand` demand
		INNER JOIN `tabLoan Repayment Schedule` repayment_schedule
			ON repayment_schedule.loan = demand.loan
		SET demand.loan_repayment_schedule = repayment_schedule.name
		WHERE IFNULL(demand.loan_repayment_schedule, "") = ""
		"""
	)


def backfill_repayment_schedule_demand_status():
	if not frappe.db.table_exists("Repayment Schedule"):
		return

	columns = frappe.db.get_table_columns("Repayment Schedule")
	if "is_accrued" not in columns or "demand_generated" not in columns:
		return

	frappe.db.sql(
		"""
		UPDATE `tabRepayment Schedule` migrated_schedule
		INNER JOIN `tabLoan Repayment Schedule` repayment_schedule
			ON repayment_schedule.name = migrated_schedule.parent
		INNER JOIN `tabRepayment Schedule` legacy_schedule
			ON legacy_schedule.parent = repayment_schedule.loan
			AND legacy_schedule.parenttype = "Loan"
			AND legacy_schedule.idx = migrated_schedule.idx
		SET migrated_schedule.demand_generated = 1
		WHERE migrated_schedule.parenttype = "Loan Repayment Schedule"
		  AND IFNULL(legacy_schedule.is_accrued, 0) = 1
		  AND IFNULL(migrated_schedule.demand_generated, 0) = 0
		"""
	)


def backfill_loan_repayment_frequency():
	if not frappe.db.has_column("Loan", "repayment_frequency"):
		return

	frappe.db.sql(
		"""
		UPDATE `tabLoan` loan
		INNER JOIN `tabLoan Repayment Schedule` repayment_schedule
			ON repayment_schedule.loan = loan.name
		SET loan.repayment_frequency = repayment_schedule.repayment_frequency
		WHERE IFNULL(loan.repayment_frequency, "") = ""
		  AND IFNULL(repayment_schedule.repayment_frequency, "") != ""
		"""
	)
