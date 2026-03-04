# Copyright (c) 2026, Alfarsi and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": "Sales Order",
            "fieldname": "sales_order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "width": 200
        },
        {
            "label": "Item",
            "fieldname": "item_display",
            "fieldtype": "Data",
            "width": 350
        },
        {
            "label": "Item Department",
            "fieldname": "custom_item_department",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Net Amount",
            "fieldname": "net_amount",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": "Billed Amount",
            "fieldname": "billed_amt",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": "Pending Amount",
            "fieldname": "pending_amount",
            "fieldtype": "Currency",
            "width": 130
        },
    ]


def get_data(filters=None):
    filters = filters or {}

    conditions = ""

    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND so.transaction_date BETWEEN %(from_date)s AND %(to_date)s"

    data = frappe.db.sql(f"""
    SELECT
        so.name AS sales_order,

        CONCAT(soi.item_code, ' - ', soi.item_name) AS item_display,

        item.custom_item_department,
                         
        COALESCE(soi.net_amount, soi.amount) AS net_amount,

        # IFNULL(SUM(sii.net_amount),0) AS billed_amount,
        SUM(
            CASE
                WHEN soi.net_amount IS NOT NULL
                    THEN IFNULL(sii.net_amount, 0)
                ELSE
                    IFNULL(sii.amount, 0)
            END
        ) AS billed_amt,


        COALESCE(soi.net_amount, soi.amount)
        - 
        SUM(
            CASE
                WHEN soi.net_amount IS NOT NULL
                    THEN IFNULL(sii.net_amount, 0)
                ELSE
                    IFNULL(sii.amount, 0)
            END
        ) AS pending_amount

    FROM `tabSales Order` so

    JOIN `tabSales Order Item` soi
        ON soi.parent = so.name
                         
    LEFT JOIN `tabItem` item
        ON item.name = soi.item_code

                
    LEFT JOIN `tabSales Invoice Item` sii
        ON (sii.sales_order = so.name AND sii.so_detail = soi.name AND sii.docstatus = 1)
    WHERE
        so.docstatus = 1
        # AND so.name = "SAL-ORD-2025-07965"
        AND so.per_billed < 100
        AND so.status NOT IN ('Closed', 'Completed')
        AND so.grand_total > 0
        # AND soi.item_code = "790016"
        {conditions}
        
    GROUP BY
        soi.name""", filters, as_dict=1,debug=1)

    return data



