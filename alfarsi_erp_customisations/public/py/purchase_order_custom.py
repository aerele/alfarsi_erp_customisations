import frappe

@frappe.whitelist()
def get_sales_order_items(supplier, customer_group=None, item_code=None):
    
    filters = {"supplier": supplier}

    query = """
        SELECT
            soi.item_code,
            soi.item_name,
            soi.uom,
            (SUM(soi.qty) - SUM(soi.delivered_qty)) AS pending_qty,
            DATEDIFF(CURDATE(), MAX(so.transaction_date)) AS aging,
            soi.parent AS sales_order
        FROM
            `tabSales Order Item` soi
        JOIN
            `tabSales Order` so ON soi.parent = so.name
        JOIN
            `tabCustomer` c ON so.customer = c.name
        WHERE
            so.docstatus = 1
            AND so.status NOT IN ('Draft', 'Cancelled', 'Completed', 'Closed')
    """

    if supplier:
        query += " AND soi.supplier = %(supplier)s"

    if customer_group:
        query += " AND c.customer_group = %(customer_group)s"
        filters["customer_group"] = customer_group

    if item_code:
        query += " AND soi.item_code = %(item_code)s"
        filters["item_code"] = item_code

    query += """ GROUP BY soi.item_code
                having pending_qty > 0
                order by pending_qty desc"""

    data = frappe.db.sql(query, filters, as_dict=1)
    return data


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_supplier_sales_order_items(doctype, txt, searchfield, start, page_len, filters):
    supplier = filters.get("supplier")

    return frappe.db.sql("""
        SELECT DISTINCT soi.item_code, soi.item_name
        FROM `tabSales Order Item` soi
        JOIN `tabSales Order` so ON soi.parent = so.name
        WHERE soi.supplier = %(supplier)s
          AND so.docstatus = 1
          AND so.status NOT IN ('Draft', 'Cancelled', 'Completed', 'Closed')
          AND (soi.qty - soi.delivered_qty) > 0
          AND soi.item_code LIKE %(txt)s
        ORDER BY soi.item_code ASC
        LIMIT %(start)s, %(page_len)s
    """, {
        "supplier": supplier,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })


