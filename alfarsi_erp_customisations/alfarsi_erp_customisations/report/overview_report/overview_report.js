// Copyright (c) 2026, Alfarsi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Overview report"] = {
	onload: function (report) {
		set_based_on_visibility(report);
	},

	filters: [
		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
		},

		{
			fieldname: "year",
			label: "Year",
			fieldtype: "Int",
			reqd: 1,
		},

		{
			fieldname: "period",
			label: "Period",
			fieldtype: "Select",
			options: ["Monthly", "Weekly", "Yearly"],
			default: "Monthly",
			reqd: 1,

			on_change: function (report) {
				set_based_on_visibility(report);
				report.refresh();
			},
		},

		{
			fieldname: "based_on",
			label: "Based On",
			fieldtype: "Select",
			options: ["Overall", "Department Wise"],
			default: "Overall",
		},
	],
};

function set_based_on_visibility(report) {
	let period = report.get_filter_value("period");

	if (period === "Monthly") {
		report.get_filter("based_on").toggle(true);
	} else {
		report.get_filter("based_on").toggle(false);
		report.set_filter_value("based_on", "Overall");
	}
}
