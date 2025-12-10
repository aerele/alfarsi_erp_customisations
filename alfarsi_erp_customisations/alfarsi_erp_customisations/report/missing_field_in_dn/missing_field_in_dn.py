import frappe

def execute(filters=None):
    columns = [
        {
            "label": "Delivery Note",
            "fieldname": "delivery_note",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Owner",
            "fieldname": "owner",
            "fieldtype": "Data",
            "width": 200
        }
    ]

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    data = frappe.db.sql(
        '''
        SELECT
            name AS delivery_note,
            owner
        FROM
            `tabDelivery Note`
        WHERE
            posting_date BETWEEN %s AND %s
            AND customer_group = "Government"
            AND ((
                    customer IN ('C01225', 'C01108')
                    AND (custom_receipt_voucher IS NULL OR custom_sign_and_stamped_dn_copy IS NULL))
                OR
                (
                    customer NOT IN ('C01225', 'C01108')
                    AND custom_sign_and_stamped_dn_copy IS NULL
                ))
            AND status IN ("To Bill", "Completed", "Closed")
        ''',
        values=(from_date, to_date),
        as_dict=1
    )

    return columns, data
