// Copyright (c) 2025, Alfarsi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Intercompany Stock Transfer", {
	refresh(frm) {
        frm.set_query("stock_in_account_booking", "table_npbv", function(frm, cdt, cdn) {
				let row = locals[cdt][cdn];
				return {
					
					filters: {
						"company": row.company,
                        "is_group":0
					}
				};
			});
         frm.set_query("stock_out_account_booking", "table_npbv", function(frm, cdt, cdn) {
				let row = locals[cdt][cdn];
				return {
					
					filters: {
						"company": row.company,
                        "is_group":0
					}
				};
			});
        

	},
});