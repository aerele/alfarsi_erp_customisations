import os
import frappe
from frappe.utils import nowdate, getdate, add_months, get_last_day
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

@frappe.whitelist()
def send_scheduled_sellout_mails():
    today = getdate(nowdate())

    settings = frappe.get_single("Brand Sellout Mail Settings")

    if int(settings.sent_mail_on) != today.day or (
        settings.last_sent_on and getdate(settings.last_sent_on) == today
    ):
        return

    first_day_last_month = getdate(f"{add_months(today, -1).year}-{add_months(today, -1).month}-01")
    last_day_last_month = get_last_day(first_day_last_month)

    if not settings.mail_configuration:
        return {"success": False}

    for mail_config in settings.mail_configuration:
        to_list = [mail.strip() for mail in mail_config.sent_mail_to.split(",")]
        cc_list = [mail.strip() for mail in mail_config.cc_to.split(",")]
        filters = {
            "from_date": first_day_last_month,
            "to_date": last_day_last_month,
            "brand": mail_config.brand,
            "include_all_items": "Need all items from the selected brand"
        }

        report = frappe.get_doc("Report", "Sellout Report")
        data = report.get_data(filters=filters)
        columns, rows = data

        # Generate Excel file
        wb = Workbook()
        ws = wb.active

        # Write headers
        for col_idx, col in enumerate(columns, 1):
            ws.cell(row=1, column=col_idx, value=col['label'])

        # Write data rows
        for row_idx, row in enumerate(rows, 2):
            if isinstance(row, dict):
                for col_idx, col in enumerate(columns, 1):
                    value = row.get(col['fieldname'], "")
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                    ws.cell(row=row_idx, column=col_idx, value=value)
            else:  # if row is a list/tuple
                for col_idx, value in enumerate(row, 1):
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                    ws.cell(row=row_idx, column=col_idx, value=value)

        file_name = f"brand_sellout_{mail_config.brand}_{today.strftime('%Y%m%d')}.xlsx"
        file_path = f"/files/{file_name}"
        full_path = os.path.join(frappe.get_site_path(), "public", file_path.lstrip("/"))

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        wb.save(full_path)

        subject = "Monthly Sellout Report"
        message = f"""
        Hi Team,

        Please find the attached sellout data for the month {add_months(today, -1).strftime('%B %Y')}.
        """

        # Attach the file and send email
        attachments = [{"file_url": file_path}]
        frappe.sendmail(
            recipients=to_list,
            cc=cc_list,
            subject=subject,
            message=message,
            attachments=attachments,
        )

    frappe.db.set_value("Brand Sellout Mail Settings", settings.name, "last_sent_on", getdate(nowdate()))
    return {"success": True}
