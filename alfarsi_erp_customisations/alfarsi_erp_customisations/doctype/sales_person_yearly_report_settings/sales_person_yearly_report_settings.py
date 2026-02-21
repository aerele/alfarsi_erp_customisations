# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import validate_email_address

class SalesPersonYearlyReportSettings(Document):
	def validate(self):
		mails_to_check = []
		if self.send_report_to:
			mails_to_check.extend(self.send_report_to.split(","))
		for email in [e.strip() for e in mails_to_check if e.strip()]:
			if not validate_email_address(email):
				frappe.throw(f"Invalid email address: {email}")