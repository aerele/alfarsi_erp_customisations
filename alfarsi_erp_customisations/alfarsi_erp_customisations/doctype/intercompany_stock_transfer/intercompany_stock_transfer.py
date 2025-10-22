# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import copy
import json
from datetime import date

import frappe
from erpnext.stock.doctype.batch.batch import get_batch_qty
from erpnext.stock.get_item_details import get_valuation_rate
from frappe.model.document import Document
from frappe.permissions import add_permission, update_permission_property
from frappe.utils import get_link_to_form

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
    permeted_roles = frappe.get_all("Role Allowed To Transfer Table",{"parent":"Intercompany Stock Transfer"},["role"],pluck ="role")
    session_role = frappe.get_all("Has Role", filters={"parent": frappe.session.user ,"role":["in",permeted_roles]}, fields=["role"],pluck ="role")
    if not session_role:
        frappe.throw("You Do Not Have Permission")
    item_list = json.loads(item_list)

    to_warehouse = {}
    item_code_list = []
    reqired_qty = {}
    for item_code in item_list:
        if item_code["qty"] > item_code["actual_qty"]:
            item_code_list += [item_code["item_code"]]
            to_warehouse[item_code["item_code"]] = item_code["warehouse"]
            if item_code["item_code"] in reqired_qty:
                reqired_qty[item_code["item_code"]] = reqired_qty[item_code["item_code"]] + (item_code["qty"] -  item_code["actual_qty"])
            reqired_qty[item_code["item_code"]] = (item_code["qty"] -  item_code["actual_qty"])
    if not item_code_list:
        frappe.msgprint("No Item Found  in another Company")
        return None 
    filter = ""
    company = frappe.get_all(
        "Intercompany Stock Transfer Table",
        {"parent": "Intercompany Stock Transfer"},
        ["company"],
        pluck="company",
    )
    if company:
        if len(company) == 1:
            filter += f" And c.name = '{company[0]}' "
        else:
            filter += f" And c.name in  {tuple(company)} "
    if len(item_code_list) == 1:
        filter += f" And bin.item_code = '{item_code_list[0]}' "
    elif len(item_code_list) >1:
        item_code_list = tuple(item_code_list)
        filter += f"And bin.item_code in {item_code_list}"
    result = frappe.db.sql(f"""select
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

                        {filter}
                        And
                        bin.actual_qty > 0
                        """,as_dict=1,debug =1) or []
        

    if result:
        new_result = []
        for details in result:
            details["to_warehouse"] = to_warehouse[details["item_code"]]
            details["reqired_qty"] = reqired_qty.get(details["item_code"])
            append_flag = True
            add_to_result = get_batch_qty(
                warehouse=details["warehouse"], item_code=details["item_code"]
            )
            for details_batch_qty in add_to_result:
                if details_batch_qty["qty"] > 0:
                    expiry_date =frappe.db.get_value("Batch",details_batch_qty["batch_no"],"expiry_date")
                    supplier_batch_no = frappe.db.get_value("Batch",details_batch_qty["batch_no"],"supplier_batch_no")
                    new_details = copy.deepcopy(details)
                    new_details["actual_qty"] = details_batch_qty["qty"]
                    new_details["batch_no"] = details_batch_qty["batch_no"]
                    new_details["expiry_date"] = expiry_date or None
                    new_details["supplier_batch_no"] = supplier_batch_no or None
                    new_result.append(new_details)
                    append_flag = False
            add_to_result = frappe.db.get_all(
                "Serial No",
                {
                    "warehouse": details["warehouse"],
                    "item_code": details["item_code"],
                    "status": "Active",
                },
                ["name", "warranty_expiry_date", "custom_supplier_serial_no"],
            )
            serial_no_flag = True
            for details_serial_qty in add_to_result:
                new_details = copy.deepcopy(details)
                new_details["actual_qty"] = 1
                new_details["serial_no"] = details_serial_qty["name"]
                new_details["expiry_date"] = (
                    details_serial_qty["warranty_expiry_date"] or None
                )
                new_details["custom_supplier_serial_no"] = (
                    details_serial_qty["custom_supplier_serial_no"] or None
                )
                new_result.append(new_details)
                serial_no_flag = False
            if append_flag and serial_no_flag:
                new_result.append(details)
        result = new_result
        return result
    frappe.msgprint("No Item Found  in another Company")
    return None


@frappe.whitelist()
def creat_intercompany_stock_transfer(transfer_details, dn, in_company,create_in_draft):
    is_enable = frappe.db.get_singles_value("Intercompany Stock Transfer", "enable")
    create_in_draft = int(create_in_draft)
    if is_enable:
        try:
            message =""
            transfer_details = json.loads(transfer_details)
            posting_date = date.today()
            posting_date = posting_date.strftime("%Y-%m-%d")
            company_wise = {}
            in_expense_account = frappe.db.get_value(
                "Intercompany Stock Transfer Table",
                {
                    "company": in_company,
                    "parent": "Intercompany Stock Transfer",
                },
                "stock_in_account_booking",
            )
            if not in_expense_account:
                frappe.throw(
                    f"stock_in_account_booking not Founed in Intercompany Stock Transfer Table for Company {in_company}"
                )
            material_receipt_doc = frappe.new_doc("Stock Entry")
            material_receipt_doc.stock_entry_type = "Material Receipt"
            material_receipt_doc.company = in_company
            material_receipt_doc.posting_date = posting_date
            material_receipt_doc.remarks = f"Material Receipt is done by {frappe.session.user} in reference to {dn} "
            for transfer_detail in transfer_details:
                transfer_detail_company = transfer_detail.get("company")
                if transfer_detail_company in company_wise:
                    company_wise[transfer_detail_company].append(transfer_detail)
                else:
                    company_wise[transfer_detail_company] = [transfer_detail]
                basic_rate = get_valuation_rate(
                    transfer_detail.get("item_code"),
                    transfer_detail_company,
                    transfer_detail.get("warehouse"),
                )
                if basic_rate and basic_rate.get("valuation_rate"):
                    basic_rate = round(
                        basic_rate.get("valuation_rate"),
                        int(frappe.db.get_default("float_precision") or 2),
                    )
                material_receipt_doc.append(
                    "items",
                    {
                        "t_warehouse": transfer_detail.get("to_warehouse"),
                        "item_code": transfer_detail.get("item_code"),
                        "qty": transfer_detail.get("transfer_qty"),
                        "batch_no": transfer_detail.get("batch_no"),
                        "expiry_date": transfer_detail.get("expiry_date"),
                        "serial_no": transfer_detail.get("serial_no"),
                        "supplier_batch_no": transfer_detail.get("supplier_batch_no"),
                        "expense_account": in_expense_account,
                        "basic_rate": basic_rate,
                        "custom_supplier_serial_no":transfer_detail.get("custom_supplier_serial_no"),
                    },
                )
            material_receipt_doc.save(ignore_permissions=True)
            message += f"""<br> <b>Material Receipt :{(get_link_to_form("Stock Entry",material_receipt_doc))} </b>"""

            for transfer_details in company_wise:
                out_expense_account = frappe.db.get_value(
                    "Intercompany Stock Transfer Table",
                    {
                        "company": transfer_details,
                        "parent": "Intercompany Stock Transfer",
                    },
                    "stock_out_account_booking",
                )
                if not out_expense_account:
                    frappe.throw(
                        f"stock_out_account_booking not Founed in Intercompany Stock Transfer Table for Company {transfer_details}"
                    )
                if transfer_details == in_company:
                    idx = transfer_detail.get("idx")
                    frappe.throw(f"Row {idx} warehouse Can not be  of the same Company")
                material_issue_doc = frappe.new_doc("Stock Entry")
                material_issue_doc.stock_entry_type = "Material Issue"
                material_issue_doc.company = transfer_details
                material_issue_doc.posting_date = posting_date
                material_issue_doc.remarks = f"Material Issue is done by {frappe.session.user} in reference to {dn} "
                for transfer_detail in company_wise[transfer_details]:
                    material_issue_doc.append(
                        "items",
                        {
                            "s_warehouse": transfer_detail.get("warehouse"),
                            "item_code": transfer_detail.get("item_code"),
                            "qty": transfer_detail.get("transfer_qty"),
                            "batch_no": transfer_detail.get("batch"),
                            "serial_no": transfer_detail.get("serial_no"),
                            "supplier_batch_no": transfer_detail.get(
                                "supplier_batch_no"
                            ),
                            "custom_supplier_serial_no":transfer_detail.get("custom_supplier_serial_no"),
                            "expiry_date": transfer_detail.get("expiry_date"),
                            "expense_account": out_expense_account,
                        },
                    )
                material_issue_doc.save(ignore_permissions=True)
                if not create_in_draft:
                    material_issue_doc.submit()
                message += f"""<br> <b>Material Issue :{(get_link_to_form("Stock Entry",material_receipt_doc))} </b>"""
            if not create_in_draft:
                material_receipt_doc.submit()
        except Exception as e:
            frappe.log_error(
                title="creat_intercompany_stock_transfer",
                message=frappe.get_traceback(with_context=1),
            )
        if not create_in_draft:
            return "Intercompany Stock Transfer is Completed refer the documents"+message
        return "Intercompany Stock Transfer documents are in Draft refer"+message

    else:
        frappe.throw("Intercompany Stock Transfer is disable")
