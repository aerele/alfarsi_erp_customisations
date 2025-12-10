frappe.ui.form.on("Lexer Import Log", {
	refresh: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button("Validate Items", () => {
				frappe.call({
					method: "alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.lexer_import_log.lexer_import_log.validate_items",
					args: { docname: frm.doc.name },
					callback(r) {
						if (r.message) {
							frappe.msgprint(r.message);
						}
						frm.reload_doc();
					},
				});
			});

			frm.add_custom_button("Create Document", function () {
				frappe.call({
					method: "alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.lexer_import_log.lexer_import_log.create_documents",
					args: { docname: frm.doc.name },
					freeze: true,
				});
			});
		}
	},
});