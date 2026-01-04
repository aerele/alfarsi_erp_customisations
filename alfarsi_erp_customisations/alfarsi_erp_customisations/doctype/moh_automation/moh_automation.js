// Copyright (c) 2025, Alfarsi and contributors
// For license information, please see license.txt

frappe.ui.form.on('MOH Automation', {
    onload(frm) {
        const po_name =
            frappe.route_options?.purchase_order ||
            frm.doc.source_purchase_order;

        if (!po_name) return;

        frappe.call({
            method: 'alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.moh_automation.moh_automation.get_po_data',
            args: { purchase_order: po_name },
            callback(r) {
                if (!r.message) return;

                frm.set_value('supplier', r.message.supplier);
                frm.clear_table('medical_devices');

                (r.message.items || []).forEach(item => {
                    let row = frm.add_child('medical_devices');
                    row.medical_device_item_code = item.item_code;
                    row.medical_device_name = item.item_name || '';
                    row.medical_device_category = item.medical_device_category || '';
                    row.medical_device_classification = item.medical_device_classification || '';
                    row.medical_device_model = item.medical_device_model || '';
                    row.moh_application_no = item.moh_application_no || '';
                    row.moh_approval_no = item.moh_approval_no || '';
                });

                frm.refresh_field('medical_devices');
                frm.save();
                
            }
        });

        if (frappe.route_options) {
            frappe.route_options = null;
        }
    },
    refresh(frm) {
        frm.add_custom_button(__('Show Unregistered Items'), function () {

            const unregistered = (frm.doc.medical_devices || [])
                .filter(r =>!r.moh_approval_no);

            if (!unregistered.length) {
                frappe.msgprint(__('No unregistered medical devices found.'));
                return;
            }

            let d = new frappe.ui.Dialog({
                title: __('Unregistered Medical Devices'),
                size: 'large',
                fields: [
                    {
                        fieldname: 'items',
                        fieldtype: 'Table',
                        cannot_add_rows: 1,
                        cannot_delete_rows: 1,
                        in_place_edit: true,
                        fields: [
                            {
                                fieldtype: 'Data',
                                fieldname: 'medical_device_item_code',
                                label: 'Item Code',
                                in_list_view: 1,
                                read_only: 1
                            },
                            {
                                fieldtype: 'Data',
                                fieldname: 'medical_device_name',
                                label: 'Item Name',
                                in_list_view: 1,
                                read_only: 1
                            },
                            {
                                fieldtype: 'Data',
                                fieldname: 'medical_device_category',
                                label: 'Category',
                                in_list_view: 1,
                                read_only: 1
                            },
                            {
                                fieldtype: 'Data',
                                fieldname: 'medical_device_classification',
                                label: 'Classification',
                                in_list_view: 1,
                                read_only: 1
                            },
                            {
                                fieldtype: 'Data',
                                fieldname: 'medical_device_model',
                                label: 'Model',
                                in_list_view: 1,
                                read_only: 1
                            }
                        ],
                        data: unregistered.map(r => ({
                            medical_device_item_code: r.medical_device_item_code,
                            medical_device_name: r.medical_device_name,
                            medical_device_category: r.medical_device_category,
                            medical_device_classification: r.medical_device_classification,
                            medical_device_model: r.medical_device_model
                        }))
                    }
                ],
                primary_action_label: __('Automate Registration'),
                primary_action() {

                    // Built-in row selection
                    const rows =
                        d.fields_dict.items.grid.get_selected_children();

                    if (!rows.length) {
                        frappe.msgprint(__('Please select at least one row.'));
                        return;
                    }

                    const payload = rows.map(r => ({
                        manufacturer_name: frm.doc.manufacturer_name,
                        manufacturer_country: frm.doc.manufacturer_country,
                        medical_device_name: r.medical_device_name,
                        medical_device_model: r.medical_device_model,
                        medical_device_category: r.medical_device_category,
                        medical_device_classification: r.medical_device_classification,
                        medical_device_item_code: r.medical_device_item_code
                    }));


                    frappe.call({
                        method: 'alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.moh_automation.moh_automation.automate_moh_registration',
                        args: { selected_items: JSON.stringify(payload) },
                        callback() {
                            frappe.msgprint(__('MOH Registration automated for selected items.'));
                            frm.reload_doc();
                            d.hide();
                        }
                    });
                }
            });

            d.show();
        }, __('Actions'));
    }
});
