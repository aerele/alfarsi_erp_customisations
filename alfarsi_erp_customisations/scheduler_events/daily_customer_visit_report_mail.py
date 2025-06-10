import frappe

def send_daily_customer_visit_reports():
    current_date = frappe.utils.today()
    start = f"{current_date} 00:00:00"
    end = f"{current_date} 23:59:59"

    visits = frappe.get_all("Customer Visit",
        filters={"date_and_time": ["between", [start, end]]},
        fields=["employee"]
    )

    distinct_employees = list({v["employee"] for v in visits if v["employee"]})
    for employee in distinct_employees:
        data = frappe.db.sql("""
            SELECT
                cv.name AS "Customer Visit ID",
                cv.date_and_time AS "Date",
                cv.employee_name AS "Employee Name",
                CONCAT(c.name, ' - ', c.customer_name) AS "Customer Name",
                cv.territory AS "Territory",
                cv.division AS "Division",
                dvd.objective_of_the_visitmeeting AS "Objective",
                dvd.outcome_of_the_visitmeeting AS "Outcome",
                dvd.action_plan AS "Action Plan",
                GROUP_CONCAT(ci.item_name SEPARATOR ', ') AS "Items Discussed",
                dvd.next_week_plan AS "Next Week Plan"
            FROM
                `tabCustomer Visit` cv
            LEFT JOIN `tabDaily Visit Details` dvd ON dvd.parent = cv.name
            LEFT JOIN `tabCustomer Visit Items` ci ON ci.parent = cv.name
            LEFT JOIN `tabCustomer` c ON c.name = cv.reference_name
            WHERE
                cv.docstatus = 1
                AND cv.employee = %(employee)s
                AND cv.date_and_time BETWEEN %(start)s AND %(end)s
            GROUP BY
                cv.name
            ORDER BY
                cv.date_and_time DESC
        """, {"employee": employee, "start": start, "end": end}, as_dict=True)


        if not data:
            continue

        columns = data[0].keys()
        table_rows = ""
        for row in data:
            table_rows += "<tr>"
            for col in columns:
                value = row[col] or ""
                table_rows += f"<td>{value}</td>"
            table_rows += "</tr>"

        html_table = f"""
            <table border="1" cellspacing="0" cellpadding="5">
                <tr>{''.join(f'<th>{col}</th>' for col in columns)}</tr>
                {table_rows}
            </table>
        """
        
        frappe.sendmail(
            recipients=["anto@alfarsi.me", "vinod@alfarsi.me", "director@alfarsi.me" ],
            subject=f"Customer Visit Report - {employee} - {data[0].get('Employee Name')} - {current_date}",
            message=f"""
                <p>Daily Customer Visit Report for <strong>{employee} - {data[0].get('Employee Name')}</strong> on <strong>{current_date}</strong>:</p>
                {html_table}
            """
        )
