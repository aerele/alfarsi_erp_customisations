# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import json
from datetime import date

import frappe
from frappe.model.document import Document


class IntercompanyStockTransfer(Document):
    pass


@frappe.whitelist()
def get_stock_in_other_companies(item_list, current_company):
    item_list = json.loads(item_list)
    result = []
    for item_code in item_list:
        item = item_code["item_code"]
        result += (
            frappe.db.sql(
                f"""select
															bin.item_code,
															i.item_name,
															bin.actual_qty,
															bin.warehouse,
															c.name as company
															from `tabBin` as bin
															join `tabWarehouse` as w on bin.warehouse = w.name
															join `tabCompany` as c on c.name = w.company
															join `tabItem` as i on i.name = bin.item_code
															where c.name != '{current_company}'
															And
															bin.item_code = '{item}'
															And
															bin.actual_qty > 0
															""",
                as_dict=1,
            )
            or []
        )
    if result:
        return result
    frappe.msgprint("No Item Found  in another Company")
    return None


@frappe.whitelist()
def creat_intercompany_stock_transfer(transfer_details):
    is_enable = frappe.db.get_singles_value("Intercompany Stock Transfer", "enable")
    if is_enable:
        transfer_details = json.loads(transfer_details)
        posting_date = date.today()
        posting_date = posting_date.strftime("%Y-%m-%d")
        for transfer_detail in transfer_details:
            material_issue_doc = frappe.new_doc("Stock Entry")
            material_issue_doc.stock_entry_type = "Material Issue"
            material_issue_doc.company = frappe.db.get_value(
                "Warehouse", transfer_detail.get("s_warehouse"), "company"
            )
            material_issue_doc.posting_date = posting_date
            batch_no = transfer_detail.get("batch")
            supplier_batch_no = expiry_date = None

            if batch_no:
                supplier_batch_no, expiry_date = frappe.db.get_value(
                    "Batch", batch_no, ("supplier_batch_no", "expiry_date")
                )
            material_issue_doc.append(
                "items",
                {
                    "s_warehouse": transfer_detail.get("s_warehouse"),
                    "item_code": transfer_detail.get("item_code"),
                    "qty": transfer_detail.get("qty"),
                    "batch_no": batch_no,
                    "supplier_batch_no": supplier_batch_no,
                    "expiry_date": expiry_date,
                    "expense_account": frappe.db.get_value(
                        "Intercompany Stock Transfer Table",
                        {
                            "company": transfer_detail.get("out_company"),
                            "parent": "Intercompany Stock Transfer",
                        },
                        "stock_in_account_booking",
                    ),
                },
            )
            material_issue_doc.save(ignore_permissions=True)
            material_issue_doc.submit()
            material_receipt_doc = frappe.new_doc("Stock Entry")
            material_receipt_doc.stock_entry_type = "Material Receipt"
            material_receipt_doc.company = frappe.db.get_value(
                "Warehouse", transfer_detail.get("t_warehouse"), "company"
            )
            material_receipt_doc.posting_date = posting_date

            material_receipt_doc.append(
                "items",
                {
                    "t_warehouse": transfer_detail.get("t_warehouse"),
                    "item_code": transfer_detail.get("item_code"),
                    "qty": transfer_detail.get("qty"),
                    "batch_no": transfer_detail.get("batch_no"),
                    "expiry_date": expiry_date,
                    "supplier_batch_no": supplier_batch_no,
                    "expense_account": frappe.db.get_value(
                        "Intercompany Stock Transfer Table",
                        {
                            "company": transfer_detail.get("in_company"),
                            "parent": "Intercompany Stock Transfer",
                        },
                        "stock_in_account_booking",
                    ),
                },
            )

            material_receipt_doc.save(ignore_permissions=True)
            material_receipt_doc.submit()
