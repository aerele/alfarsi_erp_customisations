// Copyright (c) 2026, Alfarsi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Medical Team Sales Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			reqd: 1,
		},
		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
		},
		{
			fieldname: "sales_person",
			label: "Sales Person",
			fieldtype: "Link",
			options: "Sales Person",
			reqd: 0,
			get_query: function () {
				return {
					filters: {
						department: "Medical Department - AFMS",
					},
				};
			},
		},
		{
			fieldname: "based_on",
			label: "Based On",
			fieldtype: "Select",
			options: "\nCustomer wise\nSales Person wise\nBrand Total wise\nBrand wise",
			default: "Customer",
			reqd: 1,
			on_change: function (report) {
				toggle_sales_person_reqd(report);
				report.refresh();
			},
		},
	],
	onload: function (report) {
		toggle_sales_person_reqd(report);
	},
};

function toggle_sales_person_reqd(report) {
	let based_on = report.get_filter_value("based_on");
	let sp_filter = report.get_filter("sales_person");

	if (based_on === "Customer") {
		sp_filter.df.reqd = 1;
	} else {
		sp_filter.df.reqd = 0;
	}
}
