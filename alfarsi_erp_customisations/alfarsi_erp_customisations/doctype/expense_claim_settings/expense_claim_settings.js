// Copyright (c) 2026, Alfarsi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Claim Settings", {
	refresh(frm) {
		if (frm.fields_dict.allowed_expense_accounts) {
			frm.fields_dict.allowed_expense_accounts.get_query = function () {
				//run when account must be selected
				return {
					filters: {
						root_type: "Expense",
						is_group: 0,
					},
				};
			};
		}
	},
});
