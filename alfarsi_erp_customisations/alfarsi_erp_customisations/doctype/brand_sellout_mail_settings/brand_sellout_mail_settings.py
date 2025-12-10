# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import validate_email_address
from frappe.utils import today,getdate,add_days

class BrandSelloutMailSettings(Document):
	def validate(self):
		if self.mail_configuration:
			for mail_config in self.mail_configuration:
				emails_to_check = []
				if mail_config.sent_mail_to:
					emails_to_check.extend(mail_config.sent_mail_to.split(","))

				if mail_config.cc_to:
					emails_to_check.extend(mail_config.cc_to.split(","))

				for email in [e.strip() for e in emails_to_check if e.strip()]:
					if not validate_email_address(email):
						frappe.throw(f"Invalid email address: {email} in row {mail_config.idx}")
	