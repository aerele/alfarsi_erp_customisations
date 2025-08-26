import frappe

def check_dn(doc, method):
    if doc.is_return:
        delivery_notes = frappe.db.sql(
            """
            SELECT DISTINCT soi.delivery_note 
            FROM `tabSales Invoice Item` soi
            WHERE soi.parent = %s
        """,
            (doc.name,),
            as_dict=True,
        )
        if not delivery_notes:
            return
        for delivery_note in delivery_notes:
            dn_name = delivery_note.get("delivery_note")
            if not dn_name:
                continue
            return_dn = frappe.db.get_value(
                "Delivery Note",
                {"return_against": dn_name, "is_return": 1},
                "name"
            )
            if not return_dn:
               frappe.throw("Delivery Note {0} has no return Delivery Note".format(dn_name))