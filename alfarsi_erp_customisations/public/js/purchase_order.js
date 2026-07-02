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

        frm.add_custom_button(__('Validate'), function () {
            let item_missing = [];
            let po_missing = [];
            let promises = [];

            if (!frm.doc.items || frm.doc.items.length === 0) {
                item_missing.push("No items found in Purchase Order");
            } else {

                frm.doc.items.forEach((row, index) => {

                    if (!row.item_code) return;

                    let p = frappe.call({
                        method: "frappe.client.get",
                        args: {
                            doctype: "Item",
                            name: row.item_code
                        }
                    }).then(r => {

                        let item = r.message;
                        let row_missing = [];

                        if (!item.custom_medical_device_model) {
                            row_missing.push("Medical Device Model");
                        }

                        if (!item.custom_medical_device_classification) {
                            row_missing.push("Medical Device Classification");
                        }

                        if (!item.custom_medical_device_category) {
                            row_missing.push("Medical Device Category");
                        }

                        if (!item.customs_tariff_number) {
                            row_missing.push("HS Code");
                        }

                        if (row_missing.length > 0) {
                            item_missing.push(
                                `<b>Item Row ${index + 1} (${row.item_code})</b><br> - ` +
                                row_missing.join("<br> - ")
                            );
                        }

                    });

                    promises.push(p);
                });
            }

            Promise.all(promises).then(() => {

                if (!frm.doc.custom_port_of_entry)
                    po_missing.push("Port of Entry");

                if (!frm.doc.custom_invoice_number)
                    po_missing.push("Invoice Number");

                if (!frm.doc.custom_sample_doc)
                    po_missing.push("Airway Bill / Bill of Lading");

                if (!frm.doc.custom_coo)
                    po_missing.push("Certificate of Origin");

                if (!frm.doc.custom_mdc_invoice)
                    po_missing.push("Medical Device Clearance Invoice");

                if (!frm.doc.custom_packing_list)
                    po_missing.push("Packing List");

                if (item_missing.length === 0 && po_missing.length === 0) {

                    frappe.msgprint({
                        title: __('Validation Successful'),
                        message: __('All required MOH fields are filled.'),
                        indicator: 'green'
                    });

                    return;
                }

                let message = "";

                if (item_missing.length > 0) {
                    message += `<h4 style="color:red;">Missing Item Requirements</h4>`;
                    message += item_missing.join("<br><br>");
                    message += "<br><br>";
                }

                if (po_missing.length > 0) {
                    message += `<h4 style="color:red;">Missing Purchase Order Requirements</h4>`;
                    message += " - " + po_missing.join("<br> - ");
                }

                frappe.msgprint({
                    title: __('MOH Validation Report'),
                    message: message,
                    indicator: 'red',
                    wide: true
                });

            });

        }, __('MOH'));


        frm.add_custom_button(__('Go To MOH Automation'), function () {
            frappe.new_doc('MOH Automation', {
                source_purchase_order: frm.doc.name
            });
        }, __('MOH'));


        frm.add_custom_button(__('Go To MOH Clearance'), function () {
            frappe.call({
                method: 'alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.moh_automation.moh_automation.trigger_po',
                args: { po: frm.doc.name }
            });
        }, __('MOH'));
        
    }  
});  

        

