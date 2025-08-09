frappe.ui.form.on('Quotation', {
    custom_ministry_quotation: function (frm) {
        let item_settings
        if (frm.doc.custom_ministry_quotation) {
            item_settings = {
                "Quotation Item": [
                    { fieldname: "custom_sr_no", columns: 1 },
                    { fieldname: "item_code", columns: 1 },
                    { fieldname: "qty", columns: 1 },
                    { fieldname: "custom_u_price_ro", columns: 1 },
                    { fieldname: "custom_t_price_ro", columns: 1 },
                    { fieldname: "custom_mfr_country", columns: 1 },
                    { fieldname: "custom_warranty", columns: 1 },
                    { fieldname: "custom_modelcatalogue", columns: 1 },
                    { fieldname: "custom_delivery_period", columns: 1 },
                    { fieldname: "is_alternative", columns: 1 }
                ]
            };
        } else {
            item_settings = {
                "Quotation Item": [
                    { fieldname: "customer_srno", columns: 1 },
                    { fieldname: "item_code", columns: 2 },
                    { fieldname: "qty", columns: 1 },
                    { fieldname: "standard_price", columns: 1 },
                    { fieldname: "description", columns: 1 },
                    { fieldname: "warehouse", columns: 1 },
                    { fieldname: "actual_qty", columns: 1 }
                ]
            };
        }
        frappe.model.user_settings
                .save("Quotation", "GridView", item_settings)
                .then((r) => {
                    frappe.model.user_settings["Quotation"] = r.message || r;
                    frm.fields_dict["items"].grid.reset_grid();
                    frm.fields_dict["items"].grid.refresh();
                });
    }
});

frappe.ui.form.on('Quotation Item', {
    qty: function (frm, cdt, cdn) {
        calculate_total_price(frm, cdt, cdn);
    },
    custom_u_price_ro: function (frm, cdt, cdn) {
        calculate_total_price(frm, cdt, cdn);
    }
});

function calculate_total_price(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.custom_t_price_ro = (row.qty || 0) * (row.custom_u_price_ro || 0);
    frm.refresh_field("items");
}
