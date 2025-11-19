import frappe
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def get_weekly_report_for_dn():
    #this report is only for director
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
    recipients = ["director@alfarsi.me"]
    frappe.sendmail(
        recipients=recipients,
        subject="Weekly Delivery Note Report (PDF)",
        attachments=[{
            "fname": "Weekly_Delivery_Note_Report.pdf",
            "fcontent": pdf_content
        }]
    )

    owner_map={}
    for row in data:
        owner = row.get("owner")
        dn_name = row.get("delivery_note")
        if owner not in owner_map:
            owner_map[owner] = []
        owner_map[owner].append(dn_name)

    for owner, dn_list in owner_map.items():
            table_rows = ""
            for dn in dn_list:
                table_rows += f"""
                    <tr>
                        <td style='padding:6px; border:1px solid #ccc;'>{dn}</td>
                    </tr>
                """

            html = f"""
                <h2>Pending Delivery Note Report</h2>
                <p><b>Date :</b> {from_date} to {to_date}</p>

                <table border='1' cellspacing='0' cellpadding='6'
                    style='border-collapse: collapse; width: 100%;'>
                    <thead>
                        <tr>
                            <th style='padding:8px; border:1px solid #ccc; background:#f2f2f2;'>
                                Delivery Note
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            """
            pdf_content = get_pdf(html)
            frappe.sendmail(
                recipients=[owner],
                subject=f"Pending Delivery Note Report ({from_date} to {to_date})",
                attachments=[{
                    "fname": f"Pending_DN_Report_{owner}.pdf",
                    "fcontent": pdf_content
                }],
                message = f"""
                <b>Make sure to fill the pending fields for these Delivery Notes:</b><br>
                - Receipt Voucher<br>
                - Signed & Stamped Delivery Note Copy<br><br>
                """
            )
    frappe.msgprint("Weekly PDF Report Sent Successfully.")
    return "Weekly PDF Report Sent Successfully"
