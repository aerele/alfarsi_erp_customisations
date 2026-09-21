# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CustomerDocumentEmailSettings(Document):
	def validate(self):
		if not self.enabled:
			return
		if not self.sender:
			frappe.throw(_("Sender Email Account is required before enabling automatic emails."))
		if self.pilot_mode and not self.pilot_customers:
			frappe.throw(_("Add at least one Pilot Customer before enabling pilot mode."))
