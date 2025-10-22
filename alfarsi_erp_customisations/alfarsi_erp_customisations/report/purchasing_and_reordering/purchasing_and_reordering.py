# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    return get_columns(filters), get_data(filters)


def get_columns(filters):
    sp = filters.get("select_period") or 6
    return [
        _("Item") + ":Data:260",
        _("Supplier") + ":Link/Supplier:140",
        _("SO Qty (Pending) - Govt") + ":Float:120",
        _("Current Stock") + ":Float:120",
        _("Avg Sales ({0}M, Non-Govt)").format(sp) + ":Float:160",
        _("6 Month Requirement") + ":Float:140",
        _("Total Requirement") + ":Float:140",
        _("Net Requirement") + ":Float:140",
        _("Last Purchase Order") + ":Data:220",
        _("Item Group") + ":Link/Item Group:140",
        _("Supp. Part No") + ":Data:120",
    ]


def get_data(filters):
    query = """
	WITH

	-- Group Sales Order Item lines by SO + Item, sum qty and delivered_qty per SO+Item
	so_items AS (
		SELECT
			soi.parent AS so_no,
			soi.item_code,
			SUM(soi.qty) AS total_ordered_qty,
			SUM(soi.delivered_qty) AS total_delivered_qty
		FROM `tabSales Order Item` soi
		INNER JOIN `tabSales Order` so ON so.name = soi.parent
		WHERE so.docstatus = 1
		AND so.status IN ('To Deliver', 'To Deliver and Bill', 'On Hold', 'Overdue')
		AND so.customer_group = 'Government'
		AND so.company = %(company)s
		GROUP BY soi.parent, soi.item_code
		HAVING (SUM(soi.qty) - SUM(soi.delivered_qty)) > 0
	),

	-- Calculate balance per SO+Item = total_ordered - total_delivered
	-- Then sum these balances per item_code
	so_balance AS (
		SELECT
			item_code,
			SUM(total_ordered_qty - total_delivered_qty) AS so_balance
		FROM so_items
		GROUP BY item_code
	),

	-- Avg sales (Non-Govt)
	avg_sales_data AS (
		SELECT
			sii.item_code,
			ROUND(SUM(sii.qty) / %(select_period)s, 0) AS avg_sales_x_months
		FROM `tabSales Invoice Item` sii
		LEFT JOIN `tabSales Invoice` si ON sii.parent = si.name
		WHERE si.docstatus = 1
		AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL %(select_period)s MONTH)
		AND si.customer_group != 'Government'
		AND si.customer NOT IN ('C02192', 'CO1004')
		AND si.company = %(company)s
		GROUP BY sii.item_code
	),

	-- Current stock
	stock_data AS (
		SELECT
			b.item_code,
			ROUND(SUM(b.actual_qty), 0) AS current_stock
		FROM `tabBin` b
		INNER JOIN `tabWarehouse` w ON b.warehouse = w.name
		WHERE b.warehouse NOT IN (
			'AP1-INDUSTORE - AFMS',
			'Expiry Warehouse - AFMS',
			'MAN-INDUSTORE - AFMS',
			'Stores - AFMM',
			'Stores - MDL',
			'Stores - WSDC'
		)
		AND w.company = %(company)s
		GROUP BY b.item_code
	),

	-- Last Purchase Order per item (latest excluding cancelled)
	last_po_data AS (
		SELECT
			poi.item_code,
			CONCAT('<a href="/app/purchase-order/', po.name, '" target="_blank">', po.name, '</a> - ', po.status) AS last_po_info
		FROM `tabPurchase Order Item` poi
		LEFT JOIN `tabPurchase Order` po ON po.name = poi.parent
		WHERE po.company = %(company)s
		AND po.status != 'Cancelled'
		ORDER BY po.transaction_date DESC, po.creation DESC
	)

	-- MAIN REPORT QUERY
	SELECT
		CONCAT('<a href="/app/item/', i.item_code, '" target="_blank">', i.item_code, ' - ', i.item_name, '</a>') AS "Item",

		(
			SELECT idf.default_supplier
			FROM `tabItem Default` idf
			WHERE idf.parent = i.item_code
			LIMIT 1
		) AS "Supplier",

		ROUND(COALESCE(sb.so_balance, 0), 0) AS "SO Qty (Pending) - Govt",
		ROUND(COALESCE(sd.current_stock, 0), 0) AS "Current Stock",

		COALESCE(asd.avg_sales_x_months, 0) AS "Avg Sales (%(select_period)sM, Non-Govt)",
		ROUND(COALESCE(asd.avg_sales_x_months, 0) * 6, 0) AS "6 Month Requirement",

		(
			ROUND(COALESCE(sb.so_balance, 0), 0)
			+ ROUND(COALESCE(asd.avg_sales_x_months, 0) * 6, 0)
		) AS "Total Requirement",

		GREATEST(
			(
				ROUND(COALESCE(sb.so_balance, 0), 0)
				+ ROUND(COALESCE(asd.avg_sales_x_months, 0) * 6, 0)
				- ROUND(COALESCE(sd.current_stock, 0), 0)
			), 0
		) AS "Net Requirement",

		(
			SELECT lpd.last_po_info
			FROM last_po_data lpd
			WHERE lpd.item_code = i.item_code
			LIMIT 1
		) AS "Last Purchase Order",

		i.item_group AS "Item Group",

		(
			SELECT supplier_part_no
			FROM `tabItem Supplier`
			WHERE parent = i.item_code
			LIMIT 1
		) AS "Supp. Part No"

	FROM `tabItem` i
	LEFT JOIN so_balance sb ON sb.item_code = i.item_code
	LEFT JOIN avg_sales_data asd ON asd.item_code = i.item_code
	LEFT JOIN stock_data sd ON sd.item_code = i.item_code

	WHERE
		(
			%(include_all_items)s = 'Yes (Include all items from the selected brand)'
			OR COALESCE(sb.so_balance, 0) > 0
			OR COALESCE(asd.avg_sales_x_months, 0) > 0
		)
		AND (
			%(all_brands)s = 'Yes (Include all the brand Items)'
			OR %(brand)s IS NULL
			OR i.brand = %(brand)s
		)

	GROUP BY
		i.item_code, i.item_name, i.item_group,
		asd.avg_sales_x_months, sd.current_stock, sb.so_balance

	UNION

	-- Include remaining enabled items if include_all_items = 'Yes' (EXCLUDING ones already in first query)
	SELECT
		CONCAT('<a href="/app/item/', i.item_code, '" target="_blank">', i.item_code, ' - ', i.item_name, '</a>') AS "Item",

		(
			SELECT idf.default_supplier
			FROM `tabItem Default` idf
			WHERE idf.parent = i.item_code
			LIMIT 1
		) AS "Supplier",

		0 AS "SO Qty (Pending) - Govt",
		0 AS "Current Stock",
		0 AS "Avg Sales (%(select_period)sM, Non-Govt)",
		0 AS "6 Month Requirement",
		0 AS "Total Requirement",
		0 AS "Net Requirement",

		(
			SELECT CONCAT('<a href="/app/purchase-order/', po.name, '" target="_blank">', po.name, '</a> - ', po.status)
			FROM `tabPurchase Order Item` poi
			LEFT JOIN `tabPurchase Order` po ON po.name = poi.parent
			WHERE poi.item_code = i.item_code AND po.company = %(company)s AND po.status != 'Cancelled'
			ORDER BY po.transaction_date DESC, po.creation DESC
			LIMIT 1
		) AS "Last Purchase Order",

		i.item_group AS "Item Group",

		(
			SELECT supplier_part_no
			FROM `tabItem Supplier`
			WHERE parent = i.item_code
			LIMIT 1
		) AS "Supp. Part No"

	FROM `tabItem` i
	WHERE i.disabled = 0
	AND i.item_code NOT IN (
		SELECT i1.item_code
		FROM `tabItem` i1
		LEFT JOIN so_balance sb1 ON sb1.item_code = i1.item_code
		LEFT JOIN avg_sales_data asd1 ON asd1.item_code = i1.item_code
		WHERE %(include_all_items)s = 'Yes (Include all items from the selected brand)'
			OR COALESCE(sb1.so_balance, 0) > 0
			OR COALESCE(asd1.avg_sales_x_months, 0) > 0
	)
	AND %(include_all_items)s = 'Yes (Include all items from the selected brand)'
	AND (
		%(all_brands)s = 'Yes (Include all the brand Items)'
		OR %(brand)s IS NULL
		OR i.brand = %(brand)s
	)

	ORDER BY "Net Requirement" DESC, "Item" ASC;
	"""

    return frappe.db.sql(query, filters, as_list=True)
