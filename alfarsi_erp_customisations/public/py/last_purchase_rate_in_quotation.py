import frappe

@frappe.whitelist()
def get_last_purchase_rates(items, customer=None):
    import json
    items = json.loads(items) if isinstance(items, str) else items
    result = []

    for item_code in items:
        last_rate = frappe.db.sql("""
            SELECT qi.item_code, qi.item_name, qi.rate, q.name as quotation, q.transaction_date
            FROM `tabQuotation Item` qi
            INNER JOIN `tabQuotation` q ON qi.parent = q.name
            WHERE qi.item_code = %s
              AND q.docstatus = 1
              AND q.medusa_quotation_id IS NOT NULL
              {customer_filter}
            ORDER BY q.transaction_date DESC
            LIMIT 1
        """.format(
            customer_filter = "AND q.party_name=%s" if customer else ""
        ), (item_code, customer) if customer else (item_code,), as_dict=True)

        if last_rate:
            row = last_rate[0]
            result.append({
                "item_code": row.item_code,
                "item_name": row.item_name,
                "last_rate": float(row.rate),
                "quotation": row.quotation,
                "date": row.transaction_date
            })
        else:
            result.append({
                "item_code": item_code,
                "item_name": frappe.db.get_value("Item", item_code, "item_name"),
                "last_rate": None,
                "quotation": None,
                "date": None
            })

    return result


