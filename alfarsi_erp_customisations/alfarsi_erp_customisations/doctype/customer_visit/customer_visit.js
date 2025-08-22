// Copyright (c) 2025, Alfarsi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Visit', {
    onload: function(frm) {
        let today = frappe.datetime.now_date();
        let dayName = moment(today).format('dddd');

        // Add red asterisk on Thursdays
        if (dayName === 'Thursday') {
            frm.set_df_property('coming_week_plans', 'reqd', true);
        } else {
            frm.set_df_property('coming_week_plans', 'reqd', false);
        }
    }
});