// Copyright (c) 2025, Alfarsi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["missing_field_in_dn"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -6),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -1),
            "reqd": 1
        }
    ],

};
