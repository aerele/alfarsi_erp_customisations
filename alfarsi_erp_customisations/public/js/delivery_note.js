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
							columns: 1,
						},
						{
							fieldtype: "Data",
							fieldname: "actual_qty",
							read_only: 1,
							in_list_view: 1,
							columns: 1,
							label: "Actual Qty",
						},
						{
							fieldtype: "Data",
							fieldname: "transfer_qty",
							in_list_view: 1,
							columns: 1,
							label: "Transfer_qty",
						},
						{
							fieldtype: "Link",
							fieldname: "batch_no",
							read_only: 1,
							in_list_view: 1,
							columns: 1,
							options: "Batch",
							label: "Batch",
						},
						{
							fieldtype: "Data",
							fieldname: "expiry_date",
							read_only: 1,
							in_list_view: 1,
							label: "Expiry Date",
							columns: 1,
						},
						{
							fieldtype: "Link",
							fieldname: "warehouse",
							read_only: 1,
							in_list_view: 1,
							options: "warehouse",
							label: "Warehouse",
							columns: 1,
						},
						{
							fieldtype: "Link",
							fieldname: "company",
							read_only: 1,
							in_list_view: 1,
							options: "Company",
							label: "Company",
							columns: 1,
						},
						{
							fieldtype: "Link",
							fieldname: "to_warehouse",
							label: "To Warehouse",
							options: "Warehouse",
							columns: 1,

							in_list_view: 1,
							get_query: (e) => {
								return {
									filters: {
										company: frm.doc.company,
									},
								};
							},
						},
						{
							fieldtype: "Data",
							fieldname: "supplier_batch_no",
							read_only: 1,
							label: "Supplier Batch No",
							columns: 1,
						},
						{
							fieldtype: "Link",
							fieldname: "serial_no",
							read_only: 1,
							in_list_view: 1,
							columns: 1,
							options: "Serial No",
							label: "Serial No",
						},
						{
							fieldtype: "Data",
							fieldname: "custom_supplier_serial_no",
							read_only: 1,
							label: "Supplier Serial No",
						},
						{
							fieldtype: "Data",
							fieldname: "reqired_qty",
							read_only: 1,
							label: "Reqired_qty",
						},
					];
					var data = r.message.map((d) => {
						var return_value = {
							item_code: d.item_code,
							actual_qty: d.actual_qty,
							warehouse: d.warehouse,
							company: d.company,
							item_name: d.item_name,
							batch_no: d.batch_no,
							supplier_batch_no: d.supplier_batch_no,
							expiry_date: d.expiry_date,
							to_warehouse: d.to_warehouse,
							serial_no: d.serial_no,
							custom_supplier_serial_no: d.custom_supplier_serial_no,
							reqired_qty:d.reqired_qty
						};
						if (d.serial_no) {
							return_value["transfer_qty"] = 1;
						}
						return return_value;
					});

					let dialog = new frappe.ui.Dialog({
						title: __("Stock In Other Companies"),
						size: "extra-large",
						fields: [
							{
							fieldtype: "Check",
							fieldname: "create_in_draft",
							label: "Create In Draft",
							default : 0},
							{
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
							}
						],
						primary_action: function () {
							var data =
								cur_dialog.fields_dict[
									"stock_in_other_companies"
								].grid.get_selected_children();
							
							if (!(data.length > 0)) {
								frappe.throw("select atleast one row to transfer");
							}
							var throw_message = "";
							var item_reqired_qty = {}
							for (let index = 0; index < data.length; index++) {

								if (!data[index]["transfer_qty"]) {
									throw_message =
										throw_message +
										"Transfer Qty  is Missing in Row " +
										(index + 1).toString() +
										"<br>";
								}
								if (
									data[index]["transfer_qty"] &&
									data[index]["transfer_qty"] > data[index]["actual_qty"]
								) {
									throw_message =
										throw_message +
										"Transfer Qty  Can not greater than Qctual Qty Row " +
										(index + 1).toString() +
										"<br>";
								}
								if (data[index]["item_code"] in item_reqired_qty){
									item_reqired_qty[data[index]["item_code"]]["transfer_qty"]+ data[index]["transfer_qty"]
									if (item_reqired_qty[data[index]["item_code"]]["transfer_qty"] > item_reqired_qty[data[index]["item_code"]]["reqired_qty"])
									{
										throw_message =
										throw_message +
										"Transfer Qty  Can not greater than Reqired Qty Row " +
										(index + 1).toString() +
										"<br>";
									}
								}
								else{
									item_reqired_qty[data[index]["item_code"]] = {"transfer_qty" :data[index]["transfer_qty"],"reqired_qty":  data[index]["reqired_qty"] }
									if (item_reqired_qty[data[index]["item_code"]]["transfer_qty"] > item_reqired_qty[data[index]["item_code"]]["reqired_qty"])
									{
										throw_message =
										throw_message +
										"Transfer Qty  Can not greater than Reqired Qty Row " +
										(index + 1).toString() +
										"<br>";
									}
								}
								
							}
							if (throw_message) {
								frappe.throw(throw_message);
							}
							frappe.call({
								freeze: true,
								freeze_message: __("Intercompany Stock Transferring"),
								method: "alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.intercompany_stock_transfer.intercompany_stock_transfer.creat_intercompany_stock_transfer",
								args: {
									transfer_details: data,
									dn: frm.doc.name,
									in_company: frm.doc.company,
									create_in_draft :dialog.get_value("create_in_draft")
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
				}
			},
		});
	},
	// custom_intercompany_stock_transfer: function (frm) {
	// 	var items_code = [];
	// 	for (let index = 0; index < frm.doc.items.length; index++) {
	// 		items_code.push(frm.doc.items[index].item_code);
	// 	}
	// 	const fields = [
	// 		{
	// 			fieldtype: "Link",
	// 			fieldname: "s_warehouse",
	// 			options: "Warehouse",
	// 			in_list_view: 1,
	// 			label: "From Warehouse",
	// 			reqd: 1,
	// 		},
	// 		{
	// 			fieldtype: "Link",
	// 			fieldname: "t_warehouse",
	// 			options: "Warehouse",
	// 			in_list_view: 1,
	// 			label: "To Warehouse",
	// 			reqd: 1,
	// 		},
	// 		{
	// 			fieldtype: "Link",
	// 			fieldname: "item_code",
	// 			options: "Item",
	// 			in_list_view: 1,
	// 			label: "Item Code",
	// 			reqd: 1,
	// 			get_query: () => {
	// 				return {
	// 					filters: {
	// 						name: ["in", items_code],
	// 					},
	// 				};
	// 			},
	// 		},
	// 		{
	// 			fieldtype: "Float",
	// 			fieldname: "qty",
	// 			default: 0,
	// 			read_only: 0,
	// 			in_list_view: 1,
	// 			label: __("Qty"),
	// 		},
	// 		{
	// 			fieldtype: "Link",
	// 			fieldname: "batch",
	// 			options: "Batch",
	// 			in_list_view: 1,
	// 			label: "Batch",
	// 			get_query: (e) => {
	// 				return {
	// 					filters: {
	// 						item: e.item_code,
	// 					},
	// 				};
	// 			},
	// 		},
	// 		{
	// 			fieldtype: "Text",
	// 			fieldname: "serial_no",
	// 			options: "Serial No",
	// 			in_list_view: 1,
	// 			label: "Serial No",
	// 		},
	// 	];
	// 	let dialog = new frappe.ui.Dialog({
	// 		title: __("Intercompany Stock Transfer"),
	// 		size: "extra-large",
	// 		fields: [
	// 			{
	// 				fieldname: "intercompany_stock_transfer",
	// 				fieldtype: "Table",
	// 				label: "Items",
	// 				fields: fields,
	// 			},
	// 		],
	// 		primary_action: function () {
	// 			var data = dialog.get_value("intercompany_stock_transfer");
	// 			frappe.call({
	// 				freeze: true,
	// 				freeze_message: __("Intercompany Stock Transferring"),
	// 				method: "alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.intercompany_stock_transfer.intercompany_stock_transfer.creat_intercompany_stock_transfer",
	// 				args: {
	// 					transfer_details: data,
	// 					dn: frm.doc.name,
	// 				},
	// 				callback: function (r) {
	// 					if (r.message) {
	// 						dialog.hide();
	// 						frappe.msgprint(r.message);
	// 					}
	// 				},
	// 			});
	// 		},
	// 		primary_action_label: __("Stock Transfer"),
	// 	});
	// 	dialog.show();
	// },
});
