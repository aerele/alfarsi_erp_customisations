// Copyright (c) 2026, Alfarsi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Expense claim"] = {
	tree: true,
	name_field: "name",
	parent_field: "parent",
	initial_depth: 2,
	filters: [
		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
		},
	],
};
