import frappe

def check_stock(doc, method):
    customer_email = frappe.db.get_value("Customer", doc.customer, "account_manager")
    if not customer_email:
        customer_email = "sales@alfarsi.me"

    out_of_stock_items = []
    exclude_items_in_warehouse=['AP1-INDUSTORE - AFMS','Expiry Warehouse - AFMS','MAN-INDUSTORE - AFMS','Stores - AFMM','Stores - MDL','Stores - WSDC']

    for item in doc.items:
        act_qty = item.get("actual_qty") or 0
        order_qty = item.qty
        
        if act_qty < order_qty and item.get('warehouse') not in exclude_items_in_warehouse:
            reserved_qty = order_qty - act_qty
            out_of_stock_items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "order_qty": order_qty,
                "act_qty": act_qty,
                "reserved_qty": reserved_qty
            })
    if out_of_stock_items:
        users = [customer_email, "purchase@alfarsi.me", "director@alfarsi.me"]
        rows = "".join(
            f"""
            <tr>
                <td style='border:1px solid black; padding:5px;'>{d['item_code']}</td>
                <td style='border:1px solid black; padding:5px;'>{d['item_name']}</td>
                <td style='border:1px solid black; padding:5px;'>{d['order_qty']}</td>
                <td style='border:1px solid black; padding:5px;'>{d['act_qty']}</td>
                <td style='border:1px solid black; padding:5px;'>{d['reserved_qty']}</td>
            </tr>
            """
            for d in out_of_stock_items
        )

        message = f"""
        <p>The following items are Out of Stock for Sales Order <a href='/app/sales-order/{doc.name}'>{doc.name}</a></p>
        <p>Please Take Necessary Actions</p>
        <table style='border:1px solid black; border-collapse:collapse;'>
            <tr>
                <th style='border:1px solid black; padding:5px;'>Item Code</th>
                <th style='border:1px solid black; padding:5px;'>Item Name</th>
                <th style='border:1px solid black; padding:5px;'>Ordered Quantity</th>
                <th style='border:1px solid black; padding:5px;'>Actual Quantity</th>
                <th style='border:1px solid black; padding:5px;'>Reserved Quantity</th>
            </tr>
            {rows}
        </table>
        """

        frappe.sendmail(
            recipients=users,
            subject="Stock Reservation Alert",
            message=message,
        )

        frappe.msgprint("Email sent for out of stock items.")
    else:
        frappe.msgprint("All items are in stock for this Sales Order.")
