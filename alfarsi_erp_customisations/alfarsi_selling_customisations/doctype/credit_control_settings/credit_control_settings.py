# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CreditControlSettings(Document):
	def validate(self):
		customers = [row.customers for row in self.customers]
		if len(customers) != len(set(customers)):
			frappe.throw("Duplicate customers are not allowed")

		for row in self.customers:
			if row.exclude_from_credit_control:
				row.override_limit = 0
				row.override_used = 0
				continue
			if row.override_limit < 0:
				frappe.throw(f"Override limit cannot be negative for {row.customers}")
			if row.override_limit > 10:
				frappe.throw(f"Override limit cannot exceed 10 for {row.customers}")
