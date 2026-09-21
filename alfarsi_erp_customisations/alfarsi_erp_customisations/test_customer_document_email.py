# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

from unittest import TestCase

import frappe

from alfarsi_erp_customisations.alfarsi_erp_customisations.customer_document_email import (
	get_document_configuration,
	get_eligible_customer,
	get_primary_contact_email,
	get_print_attachment,
)


class TestCustomerDocumentEmail(TestCase):
	def test_only_regular_submitted_sales_invoice_is_eligible(self):
		base = {
			"doctype": "Sales Invoice",
			"name": "SINV-0001",
			"docstatus": 1,
			"customer": "CUST-0001",
			"is_return": 0,
			"is_pos": 0,
		}

		self.assertEqual(get_eligible_customer(frappe._dict(base)), "CUST-0001")
		self.assertIsNone(get_eligible_customer(frappe._dict({**base, "docstatus": 0})))
		self.assertIsNone(get_eligible_customer(frappe._dict({**base, "is_return": 1})))
		self.assertIsNone(get_eligible_customer(frappe._dict({**base, "is_pos": 1})))

	def test_only_submitted_customer_receipt_is_eligible(self):
		base = {
			"doctype": "Payment Entry",
			"name": "ACC-PAY-0001",
			"docstatus": 1,
			"party_type": "Customer",
			"payment_type": "Receive",
			"party": "CUST-0001",
		}

		self.assertEqual(get_eligible_customer(frappe._dict(base)), "CUST-0001")
		self.assertIsNone(get_eligible_customer(frappe._dict({**base, "payment_type": "Pay"})))
		self.assertIsNone(get_eligible_customer(frappe._dict({**base, "party_type": "Supplier"})))

	def test_primary_contact_email_resolution(self):
		values = iter(["CONT-0001", "billing@example.com"])

		self.assertEqual(
			get_primary_contact_email("CUST-0001", get_value=lambda *args: next(values)),
			("CONT-0001", "billing@example.com"),
		)

	def test_invalid_primary_contact_email_is_rejected(self):
		values = iter(["CONT-0001", "not-an-email"])

		self.assertEqual(
			get_primary_contact_email("CUST-0001", get_value=lambda *args: next(values)), ("CONT-0001", None)
		)

	def test_default_print_formats(self):
		settings = frappe._dict(
			invoice_email_template=None,
			invoice_print_format=None,
			payment_receipt_email_template=None,
			payment_receipt_print_format=None,
		)

		self.assertEqual(
			get_document_configuration(settings, frappe._dict(doctype="Sales Invoice")),
			(None, "Alfarsi Invoice Print"),
		)
		self.assertEqual(
			get_document_configuration(settings, frappe._dict(doctype="Payment Entry")),
			(None, "Standard"),
		)

	def test_print_attachment_uses_document_language(self):
		attachment = get_print_attachment(
			frappe._dict(doctype="Sales Invoice", name="SINV-0001", language="ar"),
			"Alfarsi Invoice Print",
		)

		self.assertEqual(attachment["lang"], "ar")
		self.assertTrue(attachment["print_letterhead"])
