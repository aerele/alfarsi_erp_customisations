frappe.listview_settings['MOH Automation'] = {
    onload(listview) {
        if (listview.page.custom_buttons_added) return;
        listview.page.add_inner_button(__('Show Unregistered Items'), function () {
            listview.filter_area.clear();
            listview.filter_area.add([
                ['MOH Automation', 'moh_application_no', 'is', 'not set'],
                ['MOH Automation', 'moh_approval_no', 'is', 'not set']
            ]);

            listview.refresh();

            frappe.show_alert({
                message: __('Showing only unregistered items'),
                indicator: 'green'
            });
        });

        listview.page.add_inner_button(__('Automate Registration'), function () {
            let selected = listview.get_checked_items();

            if (selected.length === 0) {
                frappe.msgprint(__('Please select at least one item to automate registration.'));
                return;
            }

            frappe.call({
                method: 'alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.moh_automation.moh_automation.automate_moh_registration',
                args: {
                    selected_items: JSON.stringify(selected)
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('MOH Registration automated for selected items.'));
                        listview.refresh();
                    }
                }
            });

        });

        listview.page.custom_buttons_added = true;
    }
};
