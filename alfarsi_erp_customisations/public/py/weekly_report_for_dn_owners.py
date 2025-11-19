import frappe
from frappe.utils.pdf import get_pdf
@frappe.whitelist()
def send_pending_dn_mails():
    from_date=frappe.datetime.add_days(frappe.datetime.get_today(), -6)
    to_date=frappe.datetime.add_days(frappe.datetime.get_today(), -1)

    pending_dn = frappe.db.sql(
        '''
        SELECT 
            name,
            owner
        FROM 
            `tabDelivery Note`
        WHERE 
            posting_date BETWEEN %s AND %s 
            AND customer_group = "Government"
            AND (
                (
                    customer IN ('C01225', 'C01108') 
                    AND (custom_receipt_voucher IS NULL OR custom_sign_and_stamped_dn_copy IS NULL)
                )
                OR
                (
                    customer NOT IN ('C01225', 'C01108') 
                    AND custom_sign_and_stamped_dn_copy IS NULL
                )
            )
            AND status IN ("To Bill", "Completed", "Closed")
        ''',
        values=(from_date, to_date),
        as_dict=1
    )

    if not pending_dn:
        return "No pending Delivery Notes found."

    owners_map = {}
    for row in pending_dn:
        owner = row.owner
        dn_name = row.name

        if owner not in owners_map:
            owners_map[owner] = []
        owners_map[owner].append(dn_name)


    for owner, dn_list in owners_map.items():
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
                message=f"""
                <b>Make sure to fill the pending fields for these Delivery Notes:</b><br>
                - Receipt Voucher<br>
                - Signed & Stamped Delivery Note Copy<br><br>"""
            )

    return "Pending DN PDF Reports Sent Successfully!"