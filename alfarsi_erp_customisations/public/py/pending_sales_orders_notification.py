import frappe
from frappe.utils import get_url


def get_pending_sales_orders_sql():
    query = """
        SELECT 
            soi.parent AS sales_order,
            CONCAT(so.customer, ' - ', so.customer_name) AS customer,
            soi.item_code,
            soi.qty,
            soi.qty - soi.delivered_qty AS pending_qty,
            IFNULL(SUM(bin.actual_qty), 0) AS actual_qty,
            so.owner
        FROM `tabSales Order Item` soi
        INNER JOIN `tabSales Order` so ON so.name = soi.parent
        LEFT JOIN `tabBin` bin 
            ON bin.item_code = soi.item_code
            AND bin.warehouse NOT IN (
                'AP1-INDUSTORE - AFMS',
                'Expiry Warehouse - AFMS',
                'MAN-INDUSTORE - AFMS',
                'Stores - AFMM',
                'Stores - MDL',
                'Stores - WSDC'
            )
        WHERE 
            so.docstatus = 1
            AND so.status IN ('To Deliver', 'To Deliver and Bill')
            AND so.per_delivered < 100
            AND so.delivery_date <= DATE_SUB(CURDATE(), INTERVAL 4 DAY)
            AND (soi.qty - soi.delivered_qty) > 0
        GROUP BY soi.parent, soi.item_code
        HAVING actual_qty >= pending_qty
        ORDER BY so.owner, soi.parent
        """
    return frappe.db.sql(query, as_dict=True)


def send_notification_email():
    data = get_pending_sales_orders_sql()
    if not data:
        return

    base_url = get_url()
    email_map = {}

    for row in data:
        owner = row["owner"]
        if owner not in email_map:
            email_map[owner] = []
        email_map[owner].append(row)

    for owner, rows in email_map.items():
        html = """
        <h3>Pending Sales Orders with Available Stock (Overdue by 4+ Days)</h3>
        <table border=1 cellpadding=5 cellspacing=0>
            <tr>
                <th>Sales Order ID</th>
                <th>Customer</th>
                <th>Item Code</th>
                <th>Ordered Qty</th>
                <th>Pending Qty</th>
                <th>Available Qty to Deliver</th>
            </tr>
        """

        for row in rows:
            link = f"{base_url}/app/sales-order/{row['sales_order']}"
            html += f"""
                <tr>
                    <td><a href="{link}">{row['sales_order']}</a></td>
                    <td>{row['customer']}</td>
                    <td>{row['item_code']}</td>
                    <td>{int(row['qty'])}</td>
                    <td>{int(row['pending_qty'])}</td>
                    <td>{int(row['actual_qty'])}</td>
                </tr>
            """
        html += "</table>"
        frappe.sendmail(
            recipients=owner,
            subject="Pending Sales Orders with Available Stock (Overdue by 4+ Days)",
            message=html,
        )

    director_emails = ["store@alfarsi.me","director@alfarsi.me"]
    html = """
    <h3>All Pending Sales Orders with Available Stock (Overdue by 4+ Days)</h3>
    <table border=1 cellpadding=5 cellspacing=0>
        <tr>
            <th>Sales Order ID</th>
            <th>Customer</th>
            <th>Item Code</th>
            <th>Ordered Qty</th>
            <th>Pending Qty</th>
            <th>Available Qty to Deliver</th>
        </tr>
    """
    for row in data:
        link = f"{base_url}/app/sales-order/{row['sales_order']}"
        html += f"""
            <tr>
                <td><a href="{link}">{row['sales_order']}</a></td>
                <td>{row['customer']}</td>
                <td>{row['item_code']}</td>
                <td>{int(row['qty'])}</td>
                <td>{int(row['pending_qty'])}</td>
                <td>{int(row['actual_qty'])}</td>
            </tr>
        """
    html += "</table>"
    frappe.sendmail(
        recipients=director_emails,
        subject="All Pending Sales Orders with Available Stock (Overdue by 4+ Days)",
        message=html,
    )