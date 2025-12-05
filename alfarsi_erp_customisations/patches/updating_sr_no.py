import frappe

def execute():
    items=frappe.get_all('Quotation Item', fields=['name','customer_srno','custom_sr_no'])

    for item in items:
        old_value=item.customer_srno

        frappe.db.set_value('Quotation Item', item.name,'custom_sr_no', old_value)
    print("SR No updated successfully in Custom SR No field")
    frappe.db.commit()

    so=frappe.get_all('Sales Order Item', fields=['name','customer_srno','custom_sr_no'])
    for s in so:
        old_value=s.customer_srno

        frappe.db.set_value('Sales Order Item', s.name,'custom_sr_no', old_value)
    print("SR No updated successfully in Custom SR No field of Sales Order Item")
    frappe.db.commit()

    dn=frappe.get_all('Delivery Note Item', fields=['name','customer_srno','custom_sr_no'])
    for d in dn:
        old_value=d.customer_srno

        frappe.db.set_value('Delivery Note Item', d.name,'custom_sr_no', old_value)
    print("SR No updated successfully in Custom SR No field of Delivery Note Item")
    frappe.db.commit()

    si=frappe.get_all('Sales Invoice Item', fields=['name','customer_srno','custom_sr_no'])
    for s in si:
        old_value=s.customer_srno

        frappe.db.set_value('Sales Invoice Item', s.name,'custom_sr_no', old_value)
    print("SR No updated successfully in Custom SR No field of Sales Invoice Item")

    frappe.db.commit()