# Copyright (c) 2025, Alfarsi and Contributors
# See license.txt

from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.lexer_import_log import (
	lexer_import_log,
)


class TestLexerImportLog(FrappeTestCase):
	def test_serial_tracked_item_is_rejected(self):
		item = frappe._dict(name="SERIAL-ITEM", has_serial_no=1)

		with self.assertRaisesRegex(frappe.ValidationError, "Serial Numbers"):
			lexer_import_log.validate_item_tracking_for_lexer(item)

	def test_batch_item_without_auto_creation_is_rejected(self):
		item = frappe._dict(name="BATCH-ITEM", has_serial_no=0, has_batch_no=1, create_new_batch=0)

		with self.assertRaisesRegex(frappe.ValidationError, "not configured to create a new batch"):
			lexer_import_log.validate_item_tracking_for_lexer(item)

	def test_batch_item_without_series_is_rejected(self):
		item = frappe._dict(
			name="BATCH-ITEM",
			has_serial_no=0,
			has_batch_no=1,
			create_new_batch=1,
			batch_number_series=None,
		)

		with (
			patch.object(frappe, "get_single_value", return_value=None),
			self.assertRaisesRegex(frappe.ValidationError, "no Batch Number Series"),
		):
			lexer_import_log.validate_item_tracking_for_lexer(item)

	def test_batch_item_with_series_is_accepted(self):
		item = frappe._dict(
			name="BATCH-ITEM",
			has_serial_no=0,
			has_batch_no=1,
			create_new_batch=1,
			batch_number_series="YYYY.#######",
		)

		lexer_import_log.validate_item_tracking_for_lexer(item)

	def test_purchase_receipt_batch_is_created_and_assigned(self):
		item = Mock(item_code="BATCH-ITEM")
		purchase_receipt = Mock(items=[item], supplier="SUPPLIER-1", doctype="Purchase Receipt", name="PR-1")

		with (
			patch.object(
				frappe,
				"get_cached_value",
				return_value=frappe._dict(has_batch_no=1, has_serial_no=0),
			),
			patch.object(lexer_import_log, "make_batch", return_value="2026.0000001") as make_batch,
		):
			lexer_import_log.prepare_purchase_receipt_batches(purchase_receipt)

		make_batch.assert_called_once()
		item.db_set.assert_called_once_with({"batch_no": "2026.0000001", "use_serial_batch_fields": 1})
		self.assertEqual(item.batch_no, "2026.0000001")
		self.assertEqual(item.use_serial_batch_fields, 1)

	def test_non_batch_item_is_not_changed(self):
		item = Mock(item_code="NORMAL-ITEM")
		purchase_receipt = Mock(items=[item], supplier="SUPPLIER-1", doctype="Purchase Receipt", name="PR-1")

		with (
			patch.object(
				frappe,
				"get_cached_value",
				return_value=frappe._dict(has_batch_no=0, has_serial_no=0),
			),
			patch.object(lexer_import_log, "make_batch") as make_batch,
		):
			lexer_import_log.prepare_purchase_receipt_batches(purchase_receipt)

		make_batch.assert_not_called()
		item.db_set.assert_not_called()
