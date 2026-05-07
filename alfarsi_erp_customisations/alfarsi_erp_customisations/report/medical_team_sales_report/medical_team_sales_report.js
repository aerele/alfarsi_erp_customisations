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
			default: "AL FARSI MEDICAL SUPPLIES",
		},
		{
			fieldname: "sales_person",
			label: "Sales Person",
			fieldtype: "Select",
			reqd: 0,
			options: [""],
		},
		{
			fieldname: "based_on",
			label: "Based On",
			fieldtype: "Select",
			options: "\nCustomer wise\nSales Person wise\nBrand wise Total\nBrand wise",
			default: "Customer wise",
			reqd: 1,
			on_change: function (report) {
				toggle_sales_person_reqd(report);
				report.refresh();
			},
		},
	],
	onload: function (report) {
		toggle_sales_person_reqd(report);
		load_medical_sales_person_options(report);
	},
};

function toggle_sales_person_reqd(report) {
	let based_on = report.get_filter_value("based_on");
	let sp_filter = report.get_filter("sales_person");

	if (based_on === "Customer wise") {
		sp_filter.df.reqd = 1;
	} else {
		sp_filter.df.reqd = 0;
	}

	sp_filter.refresh();
}

function load_medical_sales_person_options(report) {
	const sales_person_filter = report.get_filter("sales_person");
	const current_value = report.get_filter_value("sales_person");

	frappe.call({
		method: "alfarsi_erp_customisations.alfarsi_erp_customisations.report.medical_team_sales_report.medical_team_sales_report.get_medical_sales_person_options",
		callback: function (response) {
			const options = ["", ...(response.message || [])];

			sales_person_filter.df.options = options;
			sales_person_filter.refresh();

			if (current_value && options.includes(current_value)) {
				report.set_filter_value("sales_person", current_value);
				return;
			}

			if (current_value) {
				report.set_filter_value("sales_person", "");
			}
		},
	});
}
