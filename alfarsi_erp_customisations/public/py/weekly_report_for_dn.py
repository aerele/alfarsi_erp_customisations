import frappe
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def get_weekly_report_for_dn():

    cur_user = frappe.session.user if frappe.session.user else "Administrator"
    cur_user_mail = frappe.get_value("User", cur_user, "email") or "admin@example.com"

    if cur_user == "Guest":
        frappe.throw("Please log in to access this feature.")

    report_name = "missing_field_in_dn"

    to_date = frappe.utils.add_days(frappe.utils.today(), -1)
    from_date = frappe.utils.add_days(to_date, -6)
    filters = {
        "from_date": from_date,
        "to_date": to_date
    }

    report = frappe.get_doc("Report", report_name)
    columns, data = report.execute_script_report(filters)

    html = "<h2>Weekly Delivery Note Report</h2>"
    html += f"<p>Report Date Range: {from_date} to {to_date}</p>"

    html += "<table border='1' cellspacing='0' cellpadding='6' style='border-collapse: collapse; width: 100%;'>"
    html += "<thead><tr>"


    for col in columns:
        html += f"<th>{col.get('label')}</th>"

    html += "</tr></thead><tbody>"
    for row in data:
        html += "<tr>"
        for col in columns:
            field = col.get("fieldname")
            value = row.get(field, "") 
            html += f"<td>{value}</td>"
        html += "</tr>"

    html += "</tbody></table>"
    pdf_content = get_pdf(html)
    recipients = [cur_user_mail, "director@alfarsi.me"]
    frappe.sendmail(
        recipients=recipients,
        subject="Weekly Delivery Note Report (PDF)",
        attachments=[{
            "fname": "Weekly_Delivery_Note_Report.pdf",
            "fcontent": pdf_content
        }]
    )

    frappe.msgprint("Weekly PDF Report Sent Successfully.")
    return "Weekly PDF Report Sent Successfully"
