frappe.ui.form.on("Delivery Note", {
	refresh: function (frm) {
		if (!frm.__islocal && frappe.model.can_create("Packing Slip") && frm.doc.docstatus != 2) {
			frm.add_custom_button(
				__("Packing Slip"),
				function () {
					frappe.model.open_mapped_doc({
						method: "alfarsi_erp_customisations.overrides.delivery_note.custom_make_packing_slip",
						frm: me.frm,
					});
				},
				__("Create")
			);
		}
	},
	custom_see_stock_in_other_companies: function (frm) {
		frappe.call({
			method: "alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.intercompany_stock_transfer.intercompany_stock_transfer.get_stock_in_other_companies",
			args: { item_list: frm.doc.items, current_company: frm.doc.company },
			freeze: true,
			freeze_message: __("Fetching Other Companies Stock"),
			callback: (r) => {
				if (r.message) {
					const fields = [
						{
							fieldtype: "Link",
							fieldname: "item_code",
							read_only: 1,
							options: "Item",
							in_list_view: 1,
							label: "Item Code",
							columns: 1,
						},
						{
							fieldtype: "Data",
							fieldname: "item_name",
							read_only: 1,
							in_list_view: 1,
							label: "Item Name",
							columns: 5,
						},
						{
							fieldtype: "Data",
							fieldname: "actual_qty",
							read_only: 1,
							in_list_view: 1,
							columns: 1,
							label: "Qctual Qty",
						},
						{
							fieldtype: "Link",
							fieldname: "warehouse",
							read_only: 1,
							in_list_view: 1,
							options: "warehouse",
							label: "Warehouse",
						},
						{
							fieldtype: "Link",
							fieldname: "company",
							read_only: 1,
							in_list_view: 1,
							options: "Company",
							label: "Company",
						},
					];
					var data = r.message.map((d) => {
						return {
							item_code: d.item_code,
							actual_qty: d.actual_qty,
							warehouse: d.warehouse,
							company: d.company,
							item_name: d.item_name,
						};
					});

					let dialog = new frappe.ui.Dialog({
						title: __("Stock In Other Companies"),
						size: "extra-large",
						fields: [
							{
								read_only: 1,
								fieldname: "stock_in_other_companies",
								fieldtype: "Table",
								label: "Items",
								cannot_add_rows: true,
								cannot_delete_rows: true,
								data: data,
								get_data: () => {
									return data;
								},
								fields: fields,
							},
						],
					});

					dialog.show();
				}
			},
		});
	},
	custom_intercompany_stock_transfer: function (frm) {
		var items_code = [];
		for (let index = 0; index < frm.doc.items.length; index++) {
			items_code.push(frm.doc.items[index].item_code);
		}
		const fields = [
			{
				fieldtype: "Link",
				fieldname: "s_warehouse",
				options: "Warehouse",
				in_list_view: 1,
				label: "From Warehouse",
				reqd: 1,
			},
			{
				fieldtype: "Link",
				fieldname: "t_warehouse",
				options: "Warehouse",
				in_list_view: 1,
				label: "To Warehouse",
				reqd: 1,
			},
			{
				fieldtype: "Link",
				fieldname: "item_code",
				options: "Item",
				in_list_view: 1,
				label: "Item Code",
				reqd: 1,
				get_query: () => {
					return {
						filters: {
							name: ["in", items_code],
						},
					};
				},
			},
			{
				fieldtype: "Float",
				fieldname: "qty",
				default: 0,
				read_only: 0,
				in_list_view: 1,
				label: __("Qty"),
			},
			{
				fieldtype: "Link",
				fieldname: "batch",
				options: "Batch",
				in_list_view: 1,
				label: "Batch",
				get_query: (e) => {
					return {
						filters: {
							item: e.item_code,
						},
					};
				},
			},
			{
				fieldtype: "Text",
				fieldname: "serial_no",
				options: "Serial No",
				in_list_view: 1,
				label: "Serial No",
			},
		];
		let dialog = new frappe.ui.Dialog({
			title: __("Intercompany Stock Transfer"),
			size: "extra-large",
			fields: [
				{
					fieldname: "intercompany_stock_transfer",
					fieldtype: "Table",
					label: "Items",
					fields: fields,
				},
			],
			primary_action: function () {
				var data = dialog.get_value("intercompany_stock_transfer");
				frappe.call({
					freeze: true,
					freeze_message: __("Intercompany Stock Transferring"),
					method: "alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.intercompany_stock_transfer.intercompany_stock_transfer.creat_intercompany_stock_transfer",
					args: {
						transfer_details: data,
						dn: frm.doc.name,
					},
					callback: function (r) {
						if (r.message) {
							dialog.hide();
							frappe.msgprint(r.message);
						}
					},
				});
			},
			primary_action_label: __("Stock Transfer"),
		});
		dialog.show();
	},
});
