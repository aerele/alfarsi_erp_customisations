import frappe
from frappe.utils import nowdate, getdate, add_months, get_last_day

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

    if settings.mail_configuration:
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
            table = build_html_table(data)

            message = f"""
            <p>Hi Team,</p>
            <p>Please find the attached sellout data.</p>
            {table}
            """
            frappe.sendmail(
                recipients=to_list,
                cc=cc_list,
                subject="Monthly Sellout Report",
                message=message,
            )
        frappe.db.set_value("Brand Sellout Mail Settings", settings.name, "last_sent_on", getdate(nowdate()))

def build_html_table(data):
    columns, rows = data

    html = '<table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse;">'

    html += "<tr>"
    for col in columns:
        html += f"<th>{col['label']}</th>"
    html += "</tr>"

    for i, row in enumerate(rows):
        is_total = isinstance(row, (list, tuple)) and row[0] == "Total"

        html += "<tr style='font-weight:bold;'>" if is_total else "<tr>"

        if isinstance(row, dict):
            for col in columns:
                value = row.get(col['fieldname'], "")

                if isinstance(value, float) and value.is_integer():
                    value = int(value)

                html += f"<td>{value}</td>"

        else:
            for value in row:
                if isinstance(value, float) and value.is_integer():
                    value = int(value)
                html += f"<td>{value}</td>"

        html += "</tr>"

    html += "</table>"
    return html
