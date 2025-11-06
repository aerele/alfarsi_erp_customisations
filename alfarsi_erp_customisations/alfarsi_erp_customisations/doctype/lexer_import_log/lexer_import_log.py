# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
class LexerImportLog(Document):
	pass

@frappe.whitelist()
def validate_items(docname):
    doc = frappe.get_doc("Lexer Import Log", docname)

    for row in doc.items:
        part_number = row.part_number
        if not part_number:
            frappe.throw(f"Part Number is missing for item: {row.item_name}")
        
        item = frappe.db.get_value(
            "Item",
            {"description": ["like", f"%{part_number}%"]},
            ["name", "item_name"],
            as_dict=True
        )

        if item:
            row.item_code = item["name"]
        else:
            new_item_name = f"Trusta {row.item_name or ''} ANE - {part_number}"
            last_code = frappe.db.sql("""
                SELECT MAX(CAST(SUBSTRING(item_code, 3) AS SIGNED))
                FROM `tabItem` WHERE item_code LIKE '38%'
            """, as_list=True)

            next_number = (last_code[0][0] or 0) + 1 if last_code else 3800001
            new_item_code = f"38{next_number}"

            new_item = frappe.get_doc({
                "doctype": "Item",
                "item_name": new_item_name,
                "item_code": new_item_code,
                "description": part_number,
                "item_group": "All Item Groups",
                "stock_uom": "Each",
                "disabled": 1,
                "profit_margin": 0
            })
            new_item.insert()
            frappe.msgprint(f"Created new Item: {new_item_code} - {new_item_name}")
    doc.save()
    doc.reload()
    return 


@frappe.whitelist()
def create_documents(docname):
    doc = frappe.get_doc("Lexer Import Log", docname)
    for row in doc.items:
        if not frappe.db.exists("Item", row.item_code):
            frappe.throw(f"Item {row.item_name} not found. Please validate the items first.")
        item_doc = frappe.get_doc("Item", row.item_code)
        if item_doc.workflow_state != 'Approved':
            frappe.throw(f"Some Items are not approved. Please approve it before continuing.")

    duplicate_reference_docs_from_settings(docname)

@frappe.whitelist()
def duplicate_reference_docs_from_settings(lexer_import_log_name):
    lexer_log = frappe.get_doc("Lexer Import Log", lexer_import_log_name)
    print("Lexer Log:", lexer_log)

    settings = frappe.get_single("Lexer Import Settings")
    reference_purchase_order = settings.reference_purchase_order
    reference_sales_order = settings.reference_sales_order

    if reference_purchase_order:
        orig_po = frappe.get_doc("Purchase Order", reference_purchase_order)
        new_po = frappe.copy_doc(orig_po)
        new_po.name = None
        new_po.items = []
        for item in lexer_log.items:
            new_po.append("items", {
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.purchase_rate
            })
        new_po.transaction_date = lexer_log.get("purchase_date")
        new_po.schedule_date = frappe.utils.nowdate()
        new_po.payment_schedule = []
        new_po.insert()
        frappe.msgprint(f"Duplicated Purchase Order: <b>{new_po.name}</b>")


        supplier_batch_no = frappe.db.get_value("Purchase Receipt Item", {}, "supplier_batch_no") or "DUMMY-BATCH-1234"
        supplier_currency = frappe.db.get_value("Supplier", new_po.supplier, "default_currency") or "DUMMY-CURRENCY"

        pr_items = []
        for item in new_po.items:
            pr_items.append({
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.rate,
                "purchase_order": new_po.name,
                "supplier_batch_no": supplier_batch_no,
                "expiry_date": frappe.utils.add_months(frappe.utils.nowdate(), 1)

            })
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": new_po.supplier,
            "posting_date": frappe.utils.nowdate(),
            "currency": supplier_currency,
            "items": pr_items,

        })
        pr.insert()
        frappe.msgprint(f"Created Purchase Receipt: <b>{pr.name}</b>")

        pi_items = []
        for item in new_po.items:
            pi_items.append({
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.rate,
                "purchase_order": new_po.name,
                "purchase_receipt": pr.name
            })

        cost_center = new_po.get("cost_center") or frappe.db.get_value("Company", new_po.company, "cost_center") or "Main - Company"
        custom_vatin_number = frappe.db.get_value("Supplier", new_po.supplier, "tax_id") or "DUMMY-TAX-ID-1234"
        custom_purchase_invoice_type = new_po.get("custom_purchase_invoice_type") or "Local Purchase"

        pi = frappe.get_doc({
            "doctype": "Purchase Invoice",
            "supplier": new_po.supplier,
            "due_date": frappe.utils.add_days(frappe.utils.nowdate(), 15),
            "bill_no": lexer_log.get("invoice_number"),
            "posting_date": frappe.utils.nowdate(),
            "bill_date":  frappe.utils.nowdate(),
            "currency": supplier_currency,
            "cost_center": cost_center,
            "custom_vatin_number": custom_vatin_number,
            "custom_purchase_invoice_type": custom_purchase_invoice_type,
            "items": pi_items

        })
        pi.insert()
        frappe.msgprint(f"Created Purchase Invoice: <b>{pi.name}</b>")

    if reference_sales_order:
        orig_so = frappe.get_doc("Sales Order", reference_sales_order)
        new_so = frappe.copy_doc(orig_so)
        new_so.name = None
        new_so.items = []
        for item in lexer_log.items:
            new_so.append("items", {
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.sales_rate
            })
        new_so.po_no= lexer_log.get("cust_po_no")
        new_so.transaction_date = lexer_log.get("sale_date")
        new_so.delivery_date = frappe.utils.nowdate()
        new_so.payment_schedule = []
        new_so.insert()
        frappe.msgprint(f"Created Sales Order: <b>{new_so.name}</b>")

        dn_items = []
        for item in new_so.items:
            matched_so_item = next(
                (so_item for so_item in new_so.items
                 if so_item.item_code == item.item_code
                 and so_item.qty == item.qty
                 and so_item.rate == item.rate),
                None
            )
            dn_items.append({
                "item_code": item.item_code,
                "qty": item.qty or 0,
                "rate": item.rate or 0,
                "sales_order": new_so.name,
                "so_detail": matched_so_item.name if matched_so_item else None,
                "against_sales_order": new_so.name
            })
  
        dn = frappe.get_doc({
            "doctype": "Delivery Note",
            "customer": new_so.customer,
            "posting_date": frappe.utils.nowdate(),
            "items": dn_items
        })
        dn.insert()
        frappe.msgprint(f"Created Delivery Note: <b>{dn.name}</b>")

        si_items = []
        for item in dn_items:
            si_items.append({
                "item_code": item["item_code"],
                "qty": item["qty"] or 0,
                "rate": item["rate"] or 0,
                "sales_order": new_so.name,
                "delivery_note": dn.name
            })
        si = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": new_so.customer,
            "due_date": frappe.utils.nowdate(),
            "items": si_items,
            "due_date": frappe.utils.add_days(frappe.utils.nowdate(), 15),
        })
        si.insert()
        frappe.msgprint(f"Created Sales Invoice: <b>{si.name}</b>")