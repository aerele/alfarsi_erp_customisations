# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import frappe
import datetime


def execute(filters=None):
	columns = get_columns()
	data = get_date(filters)
	return columns, data


def get_columns():
    return [
        {"label": "Sales Person", "fieldname": "salesperson", "fieldtype": "Link", "options": "Sales Person"},
        {"label": "Jan", "fieldname": "jan", "fieldtype": "Currency"},
        {"label": "Feb", "fieldname": "feb", "fieldtype": "Currency"},
        {"label": "Mar", "fieldname": "mar", "fieldtype": "Currency"},
        {"label": "Apr", "fieldname": "apr", "fieldtype": "Currency"},
        {"label": "May", "fieldname": "may", "fieldtype": "Currency"},
        {"label": "Jun", "fieldname": "jun", "fieldtype": "Currency"},
        {"label": "Jul", "fieldname": "jul", "fieldtype": "Currency"},
        {"label": "Aug", "fieldname": "aug", "fieldtype": "Currency"},
        {"label": "Sep", "fieldname": "sep", "fieldtype": "Currency"},
        {"label": "Oct", "fieldname": "oct", "fieldtype": "Currency"},
        {"label": "Nov", "fieldname": "nov", "fieldtype": "Currency"},
        {"label": "Dec", "fieldname": "dec", "fieldtype": "Currency"},
        {"label": "Sales Order Pending", "fieldname": "sales_order_pending", "fieldtype": "Currency"},
        {"label": "Total Sales", "fieldname": "total_sales", "fieldtype": "Currency"}
    ]

def get_date(filters=None):
    filters = filters or {}
    year = filters.get("year") or str(datetime.date.today().year)

    pinned_salespersons = [
        'Praveen P',
        'Bibin Skaria',
        'Immanuel',
        'Ginu George',
        'Ramdas'
    ]

    sales_persons = frappe.get_all("Sales Person", {"enabled" : 1}, pluck="name")
    rows = []

    for sp in sales_persons:
        sales_data = frappe.db.sql("""
            SELECT
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 1 THEN grand_total ELSE 0 END),0) AS jan,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 2 THEN grand_total ELSE 0 END),0) AS feb,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 3 THEN grand_total ELSE 0 END),0) AS mar,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 4 THEN grand_total ELSE 0 END),0) AS apr,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 5 THEN grand_total ELSE 0 END),0) AS may,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 6 THEN grand_total ELSE 0 END),0) AS jun,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 7 THEN grand_total ELSE 0 END),0) AS jul,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 8 THEN grand_total ELSE 0 END),0) AS aug,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 9 THEN grand_total ELSE 0 END),0) AS sep,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 10 THEN grand_total ELSE 0 END),0) AS oct,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 11 THEN grand_total ELSE 0 END),0) AS nov,
                COALESCE(SUM(CASE WHEN MONTH(posting_date) = 12 THEN grand_total ELSE 0 END),0) AS dec_
            FROM
                `tabSales Invoice` AS si
            JOIN
                `tabSales Team` AS st ON si.name = st.parent
            WHERE
                st.sales_person = %s
                AND YEAR(si.posting_date) = %s
                AND si.docstatus = 1
        """, (sp, year), as_dict=1)

        row = (sales_data[0] if sales_data else {
            "jan":0,"feb":0,"mar":0,"apr":0,"may":0,"jun":0,"jul":0,"aug":0,"sep":0,"oct":0,"nov":0,"dec_":0
        })
        row["salesperson"] = sp
        sales_order_pending = frappe.db.sql("""
            SELECT 
                COALESCE(SUM(grand_total), 0) AS pending_total
            FROM
                `tabSales Order` AS so
            JOIN
                `tabSales Team` AS st ON so.name = st.parent
            WHERE
                st.sales_person = %s
                AND YEAR(so.transaction_date) >= 2022
                AND so.docstatus = 1
                AND so.status != "Closed"
                AND so.per_billed < 100
        """, (sp), as_dict=1)

        row["sales_order_pending"] = sales_order_pending[0]["pending_total"] if sales_order_pending else 0
        row["total_sales"] = sum([
            row["jan"], row["feb"], row["mar"], row["apr"], row["may"], row["jun"],
            row["jul"], row["aug"], row["sep"], row["oct"], row["nov"], row["dec_"], row["sales_order_pending"]
        ])
        rows.append(row)
    
    pinned_rows = [row for row in rows if row["salesperson"] in pinned_salespersons]
    other_rows = [row for row in rows if row["salesperson"] not in pinned_salespersons]
    
    pinned_rows.sort(key=lambda x: pinned_salespersons.index(x["salesperson"]))
    other_rows.sort(key=lambda x: x["total_sales"], reverse=True)
    
    return pinned_rows + other_rows
