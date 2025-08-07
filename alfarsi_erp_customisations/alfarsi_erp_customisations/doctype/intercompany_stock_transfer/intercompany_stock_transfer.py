# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import json
from datetime import date

import frappe
from frappe.model.document import Document


class IntercompanyStockTransfer(Document):
    def validate(self):
        error = ""
        company_count = {}
        for accounts in self.table_npbv:
            company_count[accounts.company] = company_count.get(accounts.company, 0) + 1
            if (
                frappe.db.get_value(
                    "Account", accounts.stock_in_account_booking, "company"
                )
                != accounts.company
            ):
                error += f"<br >Row {accounts.idx} Account {accounts.stock_in_account_booking} is not in Company {accounts.company} <br>"
            if (
                frappe.db.get_value(
                    "Account", accounts.stock_out_account_booking, "company"
                )
                != accounts.company
            ):
                error += f"<br>Row {accounts.idx} Account {accounts.stock_out_account_booking} is not in Company {accounts.company} <br>"
        if len(company_count) != len(self.table_npbv):
            error += "<br>Company Cannot repeat<br>"
        if error:
            frappe.throw(error)


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
def creat_intercompany_stock_transfer(transfer_details, dn):
    is_enable = frappe.db.get_singles_value("Intercompany Stock Transfer", "enable")
    if is_enable:
        try:
            transfer_details = json.loads(transfer_details)
            posting_date = date.today()
            posting_date = posting_date.strftime("%Y-%m-%d")
            for transfer_detail in transfer_details:
                out_company = frappe.db.get_value(
                    "Warehouse", transfer_detail.get("s_warehouse"), "company"
                )
                out_expense_account = frappe.db.get_value(
                    "Intercompany Stock Transfer Table",
                    {
                        "company": out_company,
                        "parent": "Intercompany Stock Transfer",
                    },
                    "stock_out_account_booking",
                )
                in_company = frappe.db.get_value(
                    "Warehouse", transfer_detail.get("t_warehouse"), "company"
                )
                in_expense_account = frappe.db.get_value(
                    "Intercompany Stock Transfer Table",
                    {
                        "company": in_company,
                        "parent": "Intercompany Stock Transfer",
                    },
                    "stock_in_account_booking",
                )
                if out_company == in_company:
                    idx = transfer_detail.get("idx")
                    frappe.throw(f"Row {idx} warehouse Can not be  of the same Company")
                material_issue_doc = frappe.new_doc("Stock Entry")
                material_issue_doc.stock_entry_type = "Material Issue"
                material_issue_doc.company = out_company
                material_issue_doc.posting_date = posting_date
                material_issue_doc.remarks = f"Material Issue is done by {frappe.session.user} in reference to {dn} "
                batch_no = transfer_detail.get("batch")
                serial_no = transfer_detail.get("serial_no")
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
                        "serial_no": serial_no,
                        "supplier_batch_no": supplier_batch_no,
                        "expiry_date": expiry_date,
                        "expense_account": out_expense_account,
                    },
                )
                material_issue_doc.save(ignore_permissions=True)
                material_issue_doc.submit()
                material_receipt_doc = frappe.new_doc("Stock Entry")
                material_receipt_doc.stock_entry_type = "Material Receipt"
                material_receipt_doc.company = in_company
                material_receipt_doc.posting_date = posting_date
                material_receipt_doc.remarks = f"Material Receipt is done by {frappe.session.user} in reference to {dn} "

                material_receipt_doc.append(
                    "items",
                    {
                        "t_warehouse": transfer_detail.get("t_warehouse"),
                        "item_code": transfer_detail.get("item_code"),
                        "qty": transfer_detail.get("qty"),
                        "batch_no": transfer_detail.get("batch_no"),
                        "expiry_date": expiry_date,
                        "serial_no": serial_no,
                        "supplier_batch_no": supplier_batch_no,
                        "expense_account": in_expense_account,
                    },
                )

                material_receipt_doc.save(ignore_permissions=True)
                material_receipt_doc.submit()
        except Exception as e:
            frappe.throw(str(e))
        return "Completed"

    else:
        frappe.throw("Intercompany Stock Transfer is disable")
