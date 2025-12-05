import frappe

def execute():
    items=frappe.get_all('Quotation Item', fields=['name','customer_srno','custom_sr_no'])

    for item in items:
        old_value=item.customer_srno

        frappe.db.set_value('Quotation Item', item.name,'custom_sr_no', old_value)
    print("SR No updated successfully in Custom SR No field")
    frappe.db.commit()