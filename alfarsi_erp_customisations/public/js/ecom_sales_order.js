function et_so_apply_indicator(frm) {
	if (!frm.doc) return;

	const is_ecommerce = cint(frm.doc.from_ecommerce) === 1;
	const payment_status = frm.doc.custom_payment_status;

	if (is_ecommerce && payment_status === "Unpaid") {
		frm.page.set_indicator(__("Website Sales - Unpaid"), "red");
	}
}
frappe.ui.form.on("Sales Order", {
	onload_post_render: function (frm) {
		et_so_apply_indicator(frm);
	},
	refresh: function (frm) {
		et_so_apply_indicator(frm);
	},
});
