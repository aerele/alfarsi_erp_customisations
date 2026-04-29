// Copyright (c) 2026, Alfarsi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Account receivables yearwise"] = {
	filters: [
		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
		},
	],
};
