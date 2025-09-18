// Copyright (c) 2025, Alfarsi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Purchasing and Reordering"] = {
    "filters": [
        {
            fieldname: "company",
            label: __("Company Selection"),
            fieldtype: "Link",
            options: "Company",
            reqd: 1,
            default: "AL FARSI MEDICAL SUPPLIES"
        },
        {
            fieldname: "brand",
            label: __("Brand"),
            fieldtype: "Link",
            options: "Brand",
            reqd: 0,
            default: "BODE Chemie"
        },
        {
            fieldname: "include_all_items",
            label: __("Include all Items"),
            fieldtype: "Select",
            options: [
                "Yes (Include all items from the selected brand)",
                "No"
            ],
            reqd: 1,
            default: "No"
        },
        {
            fieldname: "all_brands",
            label: __("All Brands"),
            fieldtype: "Select",
            options: [
                "Yes (Include all the brand Items)",
                "No"
            ],
            reqd: 0,
            default: "No"
        },
        {
            fieldname: "select_period",
            label: __("Select Period"),
            fieldtype: "Select",
            options: ["1","2","3","4","5","6","7","8","9","10","11","12"],
            reqd: 1,
            default: "6"
        }
    ],
    onload: function() {
        frappe.query_report.page.add_inner_button(__("Create Purchase Order"), function() {
            let selected_indexes = frappe.query_report.datatable.rowmanager.getCheckedRows();
            let selected_rows = selected_indexes.map(i => frappe.query_report.data[i]);
            if (!selected_rows.length) {
                frappe.msgprint("No rows selected");
                return;
            }

            // Build dialog
            let d = new frappe.ui.Dialog({
                title: "Selected Items",
                size: "large",
                fields: [
                    {
                        fieldname: "items",
                        fieldtype: "Table",
                        cannot_add_rows: true,
                        in_place_edit: true,
                        data: selected_rows.map(r => ({
                            item_code: r.item,
                            supplier: r.supplier,
                            current_stock: r.current_stock || 0,
                            total_requirement: r.total_requirement || 0,
                            required_by: frappe.datetime.nowdate(),
                            rate: 0
                        })),
                        get_data: () => {
                            return d.fields_dict.items.grid.get_data();
                        },
                        fields: [
                            {
                                fieldtype: "Data",
                                fieldname: "item_code",
                                label: "Item Code",
                                in_list_view: 1,
                                read_only: 1,
                                columns: 2
                            },
                            {
                                fieldtype: "Data",
                                fieldname: "supplier",
                                label: "Supplier",
                                in_list_view: 1,
                                read_only: 1,
                                columns: 1
                            },
                            {
                                fieldtype: "Float",
                                fieldname: "current_stock",
                                label: "Current Stock",
                                in_list_view: 1,
                                read_only: 1,
                                columns: 2
                            },
                            {
                                fieldtype: "Float",
                                fieldname: "total_requirement",
                                label: "Requirement (Editable)",
                                in_list_view: 1,
                                columns: 2
                            },
                            {
                                fieldtype: "Date",
                                fieldname: "required_by",
                                label: "Required By",
                                in_list_view: 1,
                                columns: 2
                            },
                            {
                                fieldtype: "Float",
                                fieldname: "rate",
                                label: "Last Purchase Rate",
                                in_list_view: 1,
                                columns: 1,
                                reqd: 1
                            }
                        ]
                    }
                ],
                primary_action_label: "Process",
                primary_action(values) {
                    // Get edited rows
                    let items = d.fields_dict.items.grid.get_data();
                    console.log("Edited Items:", items);
                    frappe.call({
                        method: "alfarsi_erp_customisations.public.py.purchasing_and_reordering_report.create_purchase_order",
                        args: {
                            items: items
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint("Purchase Order created: " + r.message);
                                d.hide();
                                frappe.set_route("Form", "Purchase Order", r.message);
                            }
                        }
                    });
                }
            });
            d.show();

            //  Run after dialog has rendered
            setTimeout(() => {
                let table_field = d.fields_dict.items;
                let items = table_field.grid.get_data();

                items.forEach((row, idx) => {
                    // **FIXED LOGIC**: Normalize item_code correctly
                    let code = row.item_code;
                    // 1. Remove HTML tags and trim whitespace
                    code = code.replace(/<[^>]+>/g, '').trim(); 
                    
                    // 2. If a hyphen exists, split and take the first part
                    if (code.includes('-')) {
                        // Get the first element of the array, then trim it
                        code = code.split('-')[0].trim(); 
                    }

                    frappe.db.get_value("Item", {"item_code": code}, "last_purchase_rate")
                        .then(r => {
                            if (r.message && r.message.last_purchase_rate) {
                                // Update the grid data and refresh the UI
                                table_field.df.data[idx].rate = r.message.last_purchase_rate;
                                table_field.grid.refresh();
                            }
                        });
                });
            }, 300);
        });
    },
    get_datatable_options(options) {
        return Object.assign(options, {
            checkboxColumn: true
        });
    }
};
