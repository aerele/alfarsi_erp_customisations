import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt

@frappe.whitelist()
def custom_make_packing_slip(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.run_method("set_missing_values")

	def update_item(obj, target, source_parent):
		target.qty = flt(obj.qty) - flt(obj.packed_qty)

	doclist = get_mapped_doc(
		"Delivery Note",
		source_name,
		{
			"Delivery Note": {
				"doctype": "Packing Slip",
				"field_map": {"name": "delivery_note", "letter_head": "letter_head"},
                "validation": {"docstatus": ["in", [0, 1]]},
			},
			"Delivery Note Item": {
				"doctype": "Packing Slip Item",
				"field_map": {
					"item_code": "item_code",
					"item_name": "item_name",
					"batch_no": "batch_no",
					"description": "description",
					"qty": "qty",
					"stock_uom": "stock_uom",
					"name": "dn_detail",
				},
				"postprocess": update_item,
				"condition": lambda item: (
					not frappe.db.exists("Product Bundle", {"new_item_code": item.item_code, "disabled": 0})
					and flt(item.packed_qty) < flt(item.qty)
				),
			},
			"Packed Item": {
				"doctype": "Packing Slip Item",
				"field_map": {
					"item_code": "item_code",
					"item_name": "item_name",
					"batch_no": "batch_no",
					"description": "description",
					"qty": "qty",
					"name": "pi_detail",
				},
				"postprocess": update_item,
				"condition": lambda item: (flt(item.packed_qty) < flt(item.qty)),
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist