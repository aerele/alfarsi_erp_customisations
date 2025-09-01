// Copyright (c) 2025, Alfarsi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Brand Sellout Mail Settings', {
	refresh: function(frm) {
		frm.add_custom_button(__("Send Mail"), function() {
			frappe.call({
				method: "alfarsi_erp_customisations.public.py.brand_sellout_automail.send_scheduled_sellout_mails",
				callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint("Mail Sent Successfully");
                    } else {
                        frappe.msgprint("Mail not sent");
                    }
                }
			})
		})
	}
});
