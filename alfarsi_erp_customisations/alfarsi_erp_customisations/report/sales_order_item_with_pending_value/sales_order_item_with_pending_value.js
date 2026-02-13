// Copyright (c) 2026, Alfarsi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales order item with pending value"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "reqd": 1
            // "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "reqd": 1
            // "default": frappe.datetime.get_today()
        }

	]
};
