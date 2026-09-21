// Copyright (c) 2026, Alfarsi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Document Email Settings", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Emails are disabled by default. Validate templates, print formats, sender, and pilot customers before enabling."
			),
			"blue"
		);
	},
});
