import frappe
from erpnext.stock.doctype.packing_slip.packing_slip import PackingSlip

class CustomPackingSlip(PackingSlip):
	def validate_delivery_note(self):
		pass

	def validate_items(self):
		for item in self.items:
			if item.qty <= 0:
				frappe.throw(_("Row {0}: Qty must be greater than 0.").format(item.idx))

			if not item.dn_detail and not item.pi_detail:
				frappe.throw(
					_("Row {0}: Either Delivery Note Item or Packed Item reference is mandatory.").format(
						item.idx
					)
				)

			remaining_qty = frappe.db.get_value(
				"Delivery Note Item" if item.dn_detail else "Packed Item",
				{"name": item.dn_detail or item.pi_detail, "docstatus": ['in', [0, 1]]},
				["sum(qty - packed_qty)"],
			)

			if remaining_qty is None:
				frappe.throw(
					_("Row {0}: Please provide a valid Delivery Note Item or Packed Item reference.").format(
						item.idx
					)
				)
			elif remaining_qty <= 0:
				frappe.throw(
					_("Row {0}: Packing Slip is already created for Item {1}.").format(
						item.idx, frappe.bold(item.item_code)
					)
				)
			elif item.qty > remaining_qty:
				frappe.throw(
					_("Row {0}: Qty cannot be greater than {1} for the Item {2}.").format(
						item.idx, frappe.bold(remaining_qty), frappe.bold(item.item_code)
					)
				)