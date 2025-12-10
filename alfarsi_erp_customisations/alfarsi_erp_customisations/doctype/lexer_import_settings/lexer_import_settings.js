frappe.ui.form.on("Lexer Import Settings", {
    refresh(frm) {
        frm.set_query("reference_purchase_order", () => {
            return {
                filters: {
                    company: "AL FARSI MEDICAL MANUFACTURING"
                }
            };
        });

        frm.set_query("reference_sales_order", () => {
            return {
                filters: {
                    company: "AL FARSI MEDICAL MANUFACTURING"
                }
            };
        });
    }
});
