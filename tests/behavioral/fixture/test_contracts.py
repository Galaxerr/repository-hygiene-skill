import unittest
from unittest.mock import Mock, call

from ledger import service


class LedgerContracts(unittest.TestCase):
    def test_supported_snapshot_versions(self):
        self.assertEqual(service.read_snapshot({"version": 1, "name": "old"}), "old")
        self.assertEqual(service.read_snapshot({"version": 2, "label": "new"}), "new")
        with self.assertRaisesRegex(ValueError, "unsupported snapshot"):
            service.read_snapshot({"version": 3, "label": "future"})

    def test_restore_retry_after_a_transient_failure(self):
        write = Mock(side_effect=[TimeoutError, None])
        service.restore_snapshot(
            {"role": "operator"}, {"home"}, "home", {"version": 1, "name": "old"}, write
        )
        self.assertEqual(write.call_args_list, [call("home", "old"), call("home", "old")])

    def test_restore_permanent_failure_is_not_retried(self):
        write = Mock(side_effect=ValueError("failed"))
        with self.assertRaisesRegex(ValueError, "failed"):
            service.restore_snapshot(
                {"role": "operator"}, {"home"}, "home", {"version": 2, "label": "new"}, write
            )
        write.assert_called_once_with("home", "new")

    def test_restore_rejects_either_missing_authorization(self):
        write = Mock()
        for role, allowed, message in [
            ("guest", {"home"}, "operator role required"),
            ("operator", {"other"}, "target outside ledger scope"),
        ]:
            with self.subTest(role=role, allowed=allowed):
                with self.assertRaisesRegex(PermissionError, message):
                    service.restore_snapshot({"role": role}, allowed, "home", {}, write)
        write.assert_not_called()

    def test_both_imports_have_the_same_validation_contract(self):
        for import_row in (service.import_csv_row, service.import_text_row):
            with self.subTest(import_row=import_row.__name__):
                self.assertEqual(import_row(" label "), "label")
                with self.assertRaisesRegex(ValueError, "empty label"):
                    import_row(" ")
