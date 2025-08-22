frappe.ui.form.on('Quotation', {
    refresh: function (frm) {
        if(frm.doc.docstatus == 0 && frm.doc.medusa_quotation_id) {
		frm.add_custom_button(__('Get Last Sales Rate'), function(){
			frappe.call({
				method: "alfarsi_erp_customisations.public.py.last_purchase_rate_in_quotation.get_last_purchase_rates",
				args: {
					items: frm.doc.items.map(d => d.item_code),
					customer: frm.doc.party_name
				},
				callback: function(r) {
					if(r.message) {
						show_last_rates_modal(r.message, frm);
					}
				}
			});
		});
	}
    },
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



function show_last_rates_modal(data, frm) {
  let dialog = new frappe.ui.Dialog({
    title: __("Last Approved Rates"),
    fields: [
      {
        fieldname: "rates_html",
        fieldtype: "HTML",
      }
    ],
    primary_action_label: __("Use Selected Prices"),
    primary_action() {
      let selected = [];
      dialog.fields_dict.rates_html.$wrapper.find(".use-price-checkbox:checked").each(function() {
        let idx = $(this).data("idx");
        selected.push(data[idx]);
      });

      if (!selected.length) {
        frappe.msgprint(__("Please select at least one item."));
        return;
      }

      selected.forEach(row => {
        if(row.last_rate) {
          let item_row = frm.doc.items.find(i => i.item_code === row.item_code);
          if(item_row) {
            frappe.model.set_value(item_row.doctype, item_row.name, "rate", row.last_rate);
            frappe.model.set_value(item_row.doctype, item_row.name, "standard_price", row.last_rate);
						frappe.show_alert({ message: __("Selected rates applied successfully"), indicator: "green" });
          }
				} else {
					frappe.msgprint(__("No last rate found for item {0}", [row.item_name]));
        }
      });

      dialog.hide();
    }
  });

  let html = `<table class="table table-bordered">
                <thead>
                  <tr>
                    <th><input type="checkbox" id="select-all"></th>
                    <th>Item Code</th>
                    <th>Item Name</th>
                    <th>Last Rate</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>`;
  
  data.forEach((d, idx) => {
    let formatted_rate = d.last_rate !== null 
      ? format_currency(d.last_rate, frappe.defaults.get_default("currency"), 3) 
      : "-";

    html += `<tr>
               <td><input type="checkbox" class="use-price-checkbox" data-idx="${idx}"></td>
               <td>${d.item_code}</td>
               <td>${d.item_name}</td>
               <td>${formatted_rate}</td>
               <td><button class="btn btn-xs btn-primary use-price-btn" data-idx="${idx}">Use Price</button></td>
             </tr>`;
  });

  html += "</tbody></table>";
  
  dialog.fields_dict.rates_html.$wrapper.html(html);

  dialog.fields_dict.rates_html.$wrapper.find(".use-price-btn").on("click", function() {
    let idx = $(this).data("idx");
    let row = data[idx];

    if(row.last_rate) {
      let item_row = frm.doc.items.find(i => i.item_code === row.item_code);
      if(item_row) {
        frappe.model.set_value(item_row.doctype, item_row.name, "rate", row.last_rate);
        frappe.model.set_value(item_row.doctype, item_row.name, "standard_price", row.last_rate);
        frappe.show_alert({ message: __("Rate updated for {0}", [row.item_code]), indicator: "green" });
      } else {
        frappe.msgprint(__("Item {0} not found in current Quotation", [row.item_code]));
      }
    } else {
      frappe.msgprint(__("No last rate found for {0}", [row.item_code]));
    }
  });

  dialog.fields_dict.rates_html.$wrapper.find("#select-all").on("change", function() {
    let checked = $(this).prop("checked");
    dialog.fields_dict.rates_html.$wrapper.find(".use-price-checkbox").prop("checked", checked);
  });

  dialog.show();
}