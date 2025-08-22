frappe.ui.form.on("Delivery Note", {
	refresh:function(frm){
		if(
			!frm.__islocal
			&& frappe.model.can_create("Packing Slip")
			&& frm.doc.docstatus != 2
		) {
			frm.add_custom_button(
				__('Packing Slip'),
				function() {
					frappe.model.open_mapped_doc({
						method: "alfarsi_erp_customisations.overrides.delivery_note.custom_make_packing_slip",
						frm: me.frm
					});
				},
				__('Create')
			);
		}
	}
})

