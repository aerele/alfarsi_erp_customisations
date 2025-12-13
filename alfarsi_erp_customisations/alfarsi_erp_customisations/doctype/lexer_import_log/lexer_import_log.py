# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import frappe
from erpnext.stock.doctype.item.item import set_item_default
from frappe.model.document import Document
from frappe.utils import getdate


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
            {
                "item_name": ["like", "Trusta%"],
                "description": ["like", f"%{part_number}%"]
            },
            ["name", "item_name"],
            as_dict=True,
        )

        if item:
            row.item_code = item["name"]
            row.db_update()
        else:
            new_item_name = f"Trusta {row.item_name or ''} ANE - {part_number}"
            last_code = frappe.db.sql(
                """
                SELECT MAX(CAST(SUBSTRING(item_code, 4) AS UNSIGNED))
                FROM `tabItem`
                WHERE item_code LIKE '383%'
                """,
                as_list=True
            )

            next_number = (last_code[0][0] or 0) + 1 if last_code else 1
            new_item_code = f"383{next_number:04d}"

            new_item = frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_name": new_item_name,
                    "item_code": new_item_code,
                    "description": new_item_name,
                    "item_group": "All Item Groups",
                    "stock_uom": "Each",
                    "purchase_uom": "Each",
                    "sales_uom": "Each",
                    "is_stock_item": 1,
                    "disabled": 1,
                    "profit_margin": 0,
                    "has_batch_no": 1,
                    "create_new_batch": 1,
                    "batch_number_series": "YYYY.#######",
                    "brand": "Trusta"
                }
            )

            row.item_code = new_item_code
            row.db_update()
            new_item.insert()
            frappe.msgprint(f"New Item {new_item_code} created for part number {part_number}.")

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
        if item_doc.get("workflow_state") and item_doc.workflow_state != "Approved":
            frappe.throw("Some items are not approved. Please approve them before continuing.")

        set_item_default(row.item_code, "AL FARSI MEDICAL MANUFACTURING", "default_warehouse", "Stores - AFMM")

    duplicate_reference_docs_from_settings(doc)


def duplicate_reference_docs_from_settings(doc):
    settings = frappe.get_single("Lexer Import Settings")
    reference_purchase_order = settings.reference_purchase_order
    reference_sales_order = settings.reference_sales_order

    wh = "Stores - AFMM"
    company = "AL FARSI MEDICAL MANUFACTURING"

    if reference_purchase_order:
        orig_po = frappe.get_doc("Purchase Order", reference_purchase_order)

        new_po = frappe.copy_doc(orig_po)
        new_po.name = None
        new_po.company = company
        new_po.items = []
        new_po.taxes = []
        new_po.discount_amount = 0
        new_po.base_discount_amount = 0
        new_po.apply_discount_on = None
        new_po.total = 0
        new_po.base_total = 0
        new_po.net_total = 0
        new_po.base_net_total = 0
        new_po.rounded_total = 0
        new_po.base_rounded_total = 0
        new_po.grand_total = 0
        new_po.base_grand_total = 0
        new_po.currency = orig_po.currency
        new_po.supplier = orig_po.supplier

        for row in doc.items:
            item_code = str(row.item_code).split(":")[0].strip()
            new_po.append(
                "items",
                {
                    "item_code": item_code,
                    "qty": row.qty,
                    "rate": row.purchase_rate,
                    "warehouse": wh,
                },
            )

            supplier_item = frappe.get_doc("Item", item_code)
            supplier_found = None

            for s in supplier_item.get("supplier_items") or []:
                if s.get("supplier") == new_po.supplier:
                    supplier_found = s
                    break

            if supplier_found:
                if supplier_found.get("supplier_part_no") != row.part_number:
                    supplier_found.supplier_part_no = row.part_number
            else:
                supplier_item.append(
                    "supplier_items",
                    {
                        "supplier": new_po.supplier,
                        "supplier_part_no": f"ANE - {row.part_number}",
                    }
                )
            supplier_item.save()

        new_po.transaction_date = getdate(doc.get("purchase_date"))
        new_po.schedule_date = getdate(doc.get("purchase_date"))
        new_po.payment_schedule = []

        new_po.append("taxes", {
            "charge_type": "Actual",
            "account_head": "Freight Inward - AFMM",
            "cost_center": frappe.db.get_value("Company", company, "cost_center"),
            "description": "Freight Charges",
            "tax_amount": doc.purchase_tax_amount or 0
        })

        new_po.set_missing_values()
        new_po.calculate_taxes_and_totals()
        new_po.custom_lexer_doc = doc.name
        new_po.insert(ignore_permissions=True)

        frappe.set_value("Lexer Import Log", doc.name, "po_link", new_po.name)
        new_po.submit()

        supplier_currency = new_po.get("currency")
        pr_items = []
        for item in new_po.items:
            item_doc = frappe.get_doc("Item", item.item_code)
            pr_item = {
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.rate,
                "purchase_order": new_po.name,
                "supplier_batch_no": doc.get("invoice_number"),
                "expiry_date": item_doc.get("end_of_life") or None,
            }
            pr_items.append(pr_item)
        pr = frappe.get_doc(
            {
                "doctype": "Purchase Receipt",
                "company": "AL FARSI MEDICAL MANUFACTURING",
                "supplier": new_po.supplier,
                "currency": supplier_currency,
                "set_posting_time": 1,
                "posting_date": getdate(doc.get("purchase_date")),
                "items": pr_items,
            }
        )
        pr.append("taxes", {
            "charge_type": "Actual",
            "account_head": "Freight Inward - AFMM",
            "cost_center": pr.cost_center or frappe.db.get_value("Company", pr.company, "cost_center"),
            "description": "Freight Charges",
            "tax_amount": doc.purchase_tax_amount 
        })
        pr.set_missing_values()
        pr.calculate_taxes_and_totals()
        pr.insert()
        pr.custom_lexer_link_pr = doc.name
        frappe.set_value("Lexer Import Log", doc.name, "pr_link", pr.name)
        pr.submit()

        for pr_item in pr.items:
            if pr_item.batch_no:
                frappe.db.set_value("Batch", pr_item.batch_no, "batch_qty", pr_item.qty)

        pi_items = []
        for item in new_po.items:
            item_code = str(item.item_code).split(":")[0].strip()
            pi_items.append(
                {
                    "item_code": item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                    "purchase_order": new_po.name,
                    "purchase_receipt": pr.name,
                }
            )

        cost_center = frappe.db.get_value("Company", company, "cost_center")
        custom_purchase_invoice_type = new_po.get("custom_purchase_invoice_type") or "Import Purchase - Supplier"

        pi = frappe.get_doc(
            {
                "doctype": "Purchase Invoice",
                "company": company,
                "supplier": new_po.supplier,
                "set_posting_time": 1,
                "bill_no": doc.get("invoice_number"),
                "posting_date": getdate(doc.get("purchase_date")),
                "bill_date": getdate(doc.get("purchase_date")),
                "currency": supplier_currency,
                "cost_center": cost_center,
                "custom_vatin_number": doc.get("vatin_number"),
                "custom_purchase_invoice_type": custom_purchase_invoice_type,
                "items": pi_items,
            }
        )

        pi.append("taxes", {
            "charge_type": "Actual",
            "account_head": "Freight Inward - AFMM",
            "cost_center": cost_center,
            "description": "Freight Charges",
            "tax_amount": doc.purchase_tax_amount or 0
        })

        pi.set_missing_values()
        pi.calculate_taxes_and_totals()
        pi.insert()

        pi.custom_lexer_link_in_pi = doc.name
        pi.save()
        frappe.set_value("Lexer Import Log", doc.name, "pi_link", pi.name)

    if reference_sales_order:
        orig_so = frappe.get_doc("Sales Order", reference_sales_order)
        new_so = frappe.copy_doc(orig_so)

        new_so.name = None
        new_so.company = company
        new_so.items = []
        new_so.taxes = []

        new_so.discount_amount = 0
        new_so.base_discount_amount = 0
        new_so.apply_discount_on = None
        new_so.total = 0
        new_so.net_total = 0
        new_so.grand_total = 0
        new_so.rounded_total = 0
        new_so.base_total = 0
        new_so.base_net_total = 0
        new_so.base_grand_total = 0
        new_so.base_rounded_total = 0
        new_so.order_contains_free_item = 0

        new_so.workflow_state = "Draft"
        new_so.currency = orig_so.currency

        for row in doc.items:
            item_code = str(row.item_code).split(":")[0].strip()
            new_so.append(
                "items",
                {
                    "item_code": item_code,
                    "qty": row.qty,
                    "rate": row.sales_rate,
                    "warehouse": wh,
                },
            )

        new_so.po_no = doc.get("po_no")
        new_so.transaction_date = getdate(doc.get("sale_date"))
        new_so.delivery_date = getdate(doc.get("sale_date"))
        new_so.payment_schedule = []

        new_so.set_missing_values()
        new_so.calculate_taxes_and_totals()

        new_so.ignore_lexer_validation = 1
        new_so.insert(ignore_permissions=True)
        new_so.custom_lexer_link_in_so = doc.name
        new_so.save()

        frappe.set_value("Lexer Import Log", doc.name, "so_link", new_so.name)
        new_so.submit()

        dn_items = []

        for item in new_so.items:
            matched = next((i for i in new_so.items if i.item_code == item.item_code), None)

            dn_items.append(
                {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                    "warehouse": wh,
                    "sales_order": new_so.name,
                    "so_detail": matched.name,
                    "against_sales_order": new_so.name,
                    "expiry_date": frappe.db.get_value("Item", item.item_code, "end_of_life"),
                }
            )

        dn = frappe.get_doc(
            {
                "doctype": "Delivery Note",
                "company": company,
                "customer": new_so.customer,
                "currency": new_so.currency,
                "set_posting_time": 1,
                "posting_date": getdate(doc.get("sale_date")),
                "items": dn_items,
            }
        )

        dn.set_missing_values()
        dn.calculate_taxes_and_totals()
        dn.insert()

        dn.custom_lexer_link_in_dn = doc.name
        dn.save()

        frappe.set_value("Lexer Import Log", doc.name, "dn_link", dn.name)
        dn.submit()

        si_items = []

        for item in dn_items:
            si_items.append(
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "rate": item["rate"],
                    "sales_order": new_so.name,
                    "delivery_note": dn.name,
                    "expiry_date": item["expiry_date"],
                    "warehouse": wh,
                }
            )

        si = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "company": company,
                "customer": new_so.customer,
                "items": si_items,
                "currency": new_so.currency,
                "set_posting_time": 1,
                "posting_date": getdate(doc.get("sale_date")),
            }
        )

        si.set_missing_values()
        si.calculate_taxes_and_totals()

        si.insert()
        si.custom_lexer_in_si = doc.name
        si.save()

        frappe.set_value("Lexer Import Log", doc.name, "si_link", si.name)
        frappe.msgprint("All Documents Created Successfully!!")
