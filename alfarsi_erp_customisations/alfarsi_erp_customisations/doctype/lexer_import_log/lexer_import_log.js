frappe.ui.form.on('Lexer Import Log', {
    refresh: function(frm) {
        frm.add_custom_button('Validate Items', () => {
            frappe.call({
                method: "alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.lexer_import_log.lexer_import_log.validate_items",
                args: { docname: frm.doc.name },
                callback() {
                    frm.reload_doc();
                    frappe.msgprint("Item codes validated & updated successfully.");
                }
            });
        });

        frm.add_custom_button('Create Document', function() {
            frappe.call({
                method: 'alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.lexer_import_log.lexer_import_log.create_documents',
                args: {
                     docname: frm.doc.name
                   },
            });
        });
    },
});