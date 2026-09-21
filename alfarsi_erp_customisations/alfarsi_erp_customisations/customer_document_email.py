# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

from __future__ import annotations

from email.utils import formataddr

import frappe
from frappe import _
from frappe.utils import (
	escape_html,
	fmt_money,
	formatdate,
	getdate,
	validate_email_address,
)

SETTINGS_DOCTYPE = "Customer Document Email Settings"


def queue_customer_document_email(doc, method=None):
	"""Enqueue one customer email for an eligible submitted document."""
	try:
		customer = get_eligible_customer(doc)
		if not customer:
			return

		settings = frappe.get_single(SETTINGS_DOCTYPE)
		if not settings.enabled or not document_type_enabled(settings, doc.doctype):
			return
		if settings.pilot_mode and customer not in {row.customer for row in settings.pilot_customers}:
			return
		if has_existing_email(doc):
			return

		_enqueue_document(doc.doctype, doc.name)
	except Exception:
		frappe.log_error(
			title=_("Unable to queue customer document email for {0}").format(doc.name),
			message=frappe.get_traceback(),
		)


def get_eligible_customer(doc):
	if doc.docstatus != 1:
		return None

	if doc.doctype == "Sales Invoice":
		if doc.get("is_return") or doc.get("is_pos"):
			return None
		return doc.get("customer")

	if doc.doctype == "Payment Entry":
		if doc.get("party_type") != "Customer" or doc.get("payment_type") != "Receive":
			return None
		return doc.get("party")

	return None


def document_type_enabled(settings, doctype):
	return {
		"Sales Invoice": settings.send_sales_invoices,
		"Payment Entry": settings.send_payment_receipts,
	}.get(doctype, False)


def has_existing_email(doc):
	return frappe.db.exists(
		"Communication",
		{
			"reference_doctype": doc.doctype,
			"reference_name": doc.name,
			"communication_type": "Automated Message",
			"communication_medium": "Email",
		},
	)


def _enqueue_document(doctype, name):
	frappe.enqueue(
		"alfarsi_erp_customisations.alfarsi_erp_customisations.customer_document_email.process_customer_document_email",
		queue="short",
		doctype=doctype,
		name=name,
		enqueue_after_commit=True,
		now=frappe.in_test,
	)


def process_customer_document_email(doctype, name):
	from frappe.core.doctype.communication.email import _make as make_communication

	if has_existing_email(frappe._dict(doctype=doctype, name=name)):
		return

	try:
		settings = frappe.get_single(SETTINGS_DOCTYPE)
		if not settings.enabled or not document_type_enabled(settings, doctype):
			return

		doc = frappe.get_doc(doctype, name)
		customer = get_eligible_customer(doc)
		if not customer:
			return
		if settings.pilot_mode and customer not in {row.customer for row in settings.pilot_customers}:
			return

		_, recipient = get_primary_contact_email(customer)
		if not recipient:
			frappe.log_error(
				title=_("Customer document email skipped for {0}").format(name),
				message=_("Customer {0} has no primary Contact with a valid primary email address.").format(
					customer
				),
			)
			return

		template_name, print_format = get_document_configuration(settings, doc)
		sender = get_sender(settings)
		subject, message = render_email(template_name, doc, sender)
		attachments = [get_print_attachment(doc, print_format)]

		communication = make_communication(
			doctype=doc.doctype,
			name=doc.name,
			content=message,
			subject=subject,
			sender=sender,
			recipients=[recipient],
			communication_medium="Email",
			send_email=False,
			attachments=attachments,
			communication_type="Automated Message",
		).get("name")
		frappe.sendmail(
			recipients=[recipient],
			sender=sender,
			subject=subject,
			message=message,
			reference_doctype=doc.doctype,
			reference_name=doc.name,
			attachments=attachments,
			communication=communication,
			expose_recipients="header",
			print_letterhead=True,
		)
	except Exception:
		frappe.log_error(
			title=_("Unable to send customer document email for {0}").format(name),
			message=frappe.get_traceback(),
		)


def get_primary_contact_email(customer, get_value=None):
	get_value = get_value or frappe.db.get_value
	contact = get_value("Customer", customer, "customer_primary_contact")
	if not contact:
		return None, None

	email = get_value("Contact", contact, "email_id")
	validated_email = validate_email_address(email)
	return contact, validated_email or None


def get_document_configuration(settings, doc):
	if doc.doctype == "Sales Invoice":
		return settings.invoice_email_template, settings.invoice_print_format or "Alfarsi Invoice Print"
	return settings.payment_receipt_email_template, settings.payment_receipt_print_format or "Standard"


def get_sender(settings):
	account = frappe.get_cached_doc("Email Account", settings.sender)
	return formataddr((account.get("email_account_name") or account.name, account.email_id))


def render_email(template_name, doc, sender):
	if template_name:
		template = frappe.get_cached_doc("Email Template", template_name)
		document_context = doc.as_dict()
		template_context = {**document_context, "doc": document_context, **get_template_context(doc)}
		formatted = template.get_formatted_email(template_context, sender=sender)
		return formatted["subject"], formatted["message"]

	company = escape_html(doc.get("company") or "")
	customer_name = escape_html(doc.get("customer_name") or doc.get("party_name") or doc.get("party") or "")
	document_label = _("Sales Invoice") if doc.doctype == "Sales Invoice" else _("Payment Receipt")

	subject = _("{0} {1} from {2}").format(document_label, doc.name, doc.get("company") or "")
	message = _(
		"<p>Dear {0},</p><p>Please find attached {1} <strong>{2}</strong>.</p>" "<p>Regards,<br>{3}</p>"
	).format(customer_name, document_label, escape_html(doc.name), company)
	return subject, message


def get_template_context(doc):
	customer = doc.get("customer") or doc.get("party")
	contact_name = doc.get("customer_name") or doc.get("party_name") or customer or ""
	if doc.get("contact_person"):
		contact_name = frappe.db.get_value("Contact", doc.contact_person, "full_name") or contact_name

	if doc.doctype == "Sales Invoice":
		vatin = doc.get("company_tax_id") or frappe.db.get_value("Company", doc.company, "tax_id") or ""
		return {
			"customer_contact_name": contact_name,
			"company_vatin": vatin,
			"formatted_invoice_date": formatdate(doc.posting_date) if doc.get("posting_date") else "",
			"formatted_due_date": formatdate(doc.due_date) if doc.get("due_date") else "",
			"formatted_amount_due": fmt_money(
				doc.get("outstanding_amount") or 0, currency=doc.get("currency")
			),
		}

	if doc.doctype == "Payment Entry":
		return {
			"customer_contact_name": contact_name,
			"formatted_payment_date": formatdate(doc.posting_date) if doc.get("posting_date") else "",
			"formatted_amount_received": fmt_money(
				doc.get("received_amount") or doc.get("paid_amount") or 0,
				currency=doc.get("paid_currency") or doc.get("received_currency"),
			),
			"outstanding_details": get_customer_outstanding_details(customer, doc.company),
		}

	return {}


def get_customer_outstanding_details(customer, company):
	if not customer:
		return "None"
	today = getdate()
	rows = frappe.get_all(
		"Sales Invoice",
		filters={
			"customer": customer,
			"company": company,
			"docstatus": 1,
			"outstanding_amount": [">", 0],
			"due_date": ["<=", today],
		},
		fields=["name", "outstanding_amount", "due_date", "currency"],
		order_by="due_date, name",
	)
	if not rows:
		return "None"
	return "<br>".join(
		_("{0}: {1} ({2} days overdue)").format(
			row.name,
			fmt_money(row.outstanding_amount, currency=row.currency),
			max((today - getdate(row.due_date)).days, 0) if row.due_date else 0,
		)
		for row in rows
	)


def get_print_attachment(doc, print_format):
	return {
		"print_format_attachment": 1,
		"doctype": doc.doctype,
		"name": doc.name,
		"print_format": print_format,
		"print_letterhead": True,
		"lang": doc.get("language") or "en",
	}
