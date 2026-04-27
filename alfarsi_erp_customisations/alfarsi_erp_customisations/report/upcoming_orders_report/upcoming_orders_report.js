// Copyright (c) 2026, Alfarsi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Upcoming orders report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
		},
		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "department",
			label: "Department",
			fieldtype: "Data",
		},
		{
			fieldname: "sales_person",
			label: "Salesperson",
			fieldtype: "Link",
			options: "Sales Person",
		},
	],
};
