frappe.ui.form.on("Purchase Order", {
    refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Sales Order'), function() {

                let d = new frappe.ui.Dialog({
                    title: 'Select Sales Orders Items',
                    size: 'large',
                    fields: [
                        {
                            fieldtype: 'Link',
                            fieldname: 'item_code',
                            label: 'Item Code',
                            options: 'Item',
                            get_query: function() {
                                let supplier = d.get_value("supplier");
                                if (!supplier) return {};
                                return {
                                    query: "alfarsi_erp_customisations.public.py.purchase_order_custom.get_supplier_sales_order_items",
                                    filters: { supplier: supplier }
                                };
                            },
                            onchange: function() {
                                fetch_sales_order_items(frm, d);
                            }
                        },
                        { fieldtype: 'Column Break' },
                        {
                            fieldtype: 'Link',
                            fieldname: 'customer_group',
                            label: 'Customer Group',
                            options: 'Customer Group',
                            onchange: function() {
                                fetch_sales_order_items(frm, d);
                            }
                        },
                        { fieldtype: 'Column Break' },
                        {
                            fieldtype: 'Link',
                            fieldname: 'supplier',
                            label: 'Supplier',
                            options: 'Supplier',
                            default: frm.doc.supplier || "",
                            onchange: function() {
                                fetch_sales_order_items(frm, d);
                            }
                        },
                        { fieldtype: 'Section Break' },
                        {
                            fieldname: 'sales_order_mapping',
                            fieldtype: 'Table',
                            label: 'Items',
                            cannot_add_rows: 1,
                            cannot_delete_rows: 1,
                            in_place_edit: true,
                            data: [],
                            fields: [
                                { fieldtype: 'Data', fieldname: 'item_code', label: 'Item Code', in_list_view: 1, read_only: 1 },
                                { fieldtype: 'Data', fieldname: 'item_name', label: 'Item Name', in_list_view: 1, read_only: 1 },
                                { fieldtype: 'Int', fieldname: 'pending_qty', label: 'Pending Qty', in_list_view: 1, read_only: 1 },
                                { fieldtype: 'Int', fieldname: 'to_order_qty', label: 'To Order Qty', in_list_view: 1 },
                                { fieldtype: 'Int', fieldname: 'aging', label: 'Aging (Days)', in_list_view: 1, read_only: 1 },
                            ]
                        }
                    ],
                    primary_action_label: "Add Items",
                    primary_action() {
                        let values = d.get_values();

                        if (!values.supplier) return;
                        if (!frm.doc.supplier) frm.set_value("supplier", values.supplier);

                        let selected_rows = d.fields_dict.sales_order_mapping.grid.get_selected_children();
                        if (!selected_rows.length) {
                            frappe.msgprint(__('Please select at least one row.'));
                            return;
                        }

                        selected_rows.forEach(row => {
                            let child = frm.add_child("items");
                            child.item_code = row.item_code;
                            child.item_name = row.item_name;
                            child.qty = row.to_order_qty || row.pending_qty;
                            child.uom = row.uom;
                        });

                        // Remove empty rows
                        frm.doc.items = frm.doc.items.filter(item => item.item_code);

                        frm.refresh_field("items");
                        d.hide();
                    }
                });

                d.show();

                fetch_sales_order_items(frm, d);

                function fetch_sales_order_items(frm, dialog) {
                    let values = dialog.get_values();
                    if (!values.supplier) return;

                    frappe.call({
                        method: "alfarsi_erp_customisations.public.py.purchase_order_custom.get_sales_order_items",
                        args: {
                            supplier: values.supplier,
                            customer_group: values.customer_group || null,
                            item_code: values.item_code || null
                        },
                        callback: function(r) {
                            if (r.message) {
                                dialog.fields_dict.sales_order_mapping.df.data = r.message.map(row => ({
                                    __checked: 0,
                                    item_code: row.item_code,
                                    item_name: row.item_name,
                                    pending_qty: row.pending_qty,
                                    to_order_qty: row.pending_qty,
                                    aging: row.aging,
                                    uom: row.uom
                                }));
                                dialog.fields_dict.sales_order_mapping.grid.refresh();
                            } else {
                                dialog.fields_dict.sales_order_mapping.df.data = [];
                                dialog.fields_dict.sales_order_mapping.grid.refresh();
                                frappe.msgprint(__('No matching Sales Orders found.'));
                            }
                        }
                    });
                }

            }, __('Get Items From'));
        }
       if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Go To MOH Automation'), function () {
                frappe.new_doc('MOH Automation', { source_purchase_order: frm.doc.name });
            });
        }
    }
});
