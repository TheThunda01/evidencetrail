"""Column mapping must remain explicit and leave original research data intact."""

import unittest

import pandas as pd

from evidencetrail.audit import REQUIRED_COLUMNS, audit_table
from evidencetrail.mapping import map_columns, suggest_mapping


class MappingTests(unittest.TestCase):
    def test_suggestions_use_exact_headers_only(self):
        frame = pd.DataFrame(columns=[" record_id ", "Report ID", "field", "Value"])
        suggestions = suggest_mapping(frame)
        self.assertEqual(suggestions["record_id"], "record_id")
        self.assertEqual(suggestions["field"], "field")
        self.assertIsNone(suggestions["report_id"])
        self.assertIsNone(suggestions["value"])
        self.assertEqual(tuple(suggestions), REQUIRED_COLUMNS)

    def test_mapping_preserves_order_values_types_index_and_extra_columns(self):
        names = ["ID", "Report", "Question", "Answer", "Evidence", "Location", "Review"]
        frame = pd.DataFrame([
            ["001", "P1", "setting", " NA ", "Reported", "page 1", " Pending "],
            ["002", "P2", "count", 0, "Reported", "page 2", "Verified"],
        ], columns=names, index=[10, 20])
        frame.insert(2, " notes ", ["first", "second"])
        original = frame.copy(deep=True)
        mapping = dict(zip(REQUIRED_COLUMNS, names))
        mapped = map_columns(frame, mapping)
        expected_columns = ["record_id", "report_id", "notes", *REQUIRED_COLUMNS[2:]]
        self.assertEqual(mapped.columns.tolist(), expected_columns)
        self.assertEqual(mapped["value"].tolist(), [" NA ", 0])
        self.assertEqual(mapped.index.tolist(), [10, 20])
        self.assertFalse(audit_table(mapped).findings)
        pd.testing.assert_frame_equal(frame, original)
        self.assertEqual(mapping, dict(zip(REQUIRED_COLUMNS, names)))
        mapped.iloc[0, 0] = "edited copy"
        pd.testing.assert_frame_equal(frame, original)

    def test_identity_mapping_is_a_copy_and_trims_only_headers(self):
        frame = pd.DataFrame([[" x "] * 7], columns=[f" {c} " for c in REQUIRED_COLUMNS])
        mapped = map_columns(frame, dict(zip(REQUIRED_COLUMNS, REQUIRED_COLUMNS)))
        self.assertEqual(mapped.columns.tolist(), list(REQUIRED_COLUMNS))
        self.assertEqual(mapped.iloc[0].tolist(), [" x "] * 7)
        self.assertEqual(frame.columns[0], " record_id ")

    def test_incomplete_ambiguous_and_colliding_mappings_are_rejected(self):
        frame = pd.DataFrame(columns=[*REQUIRED_COLUMNS, "custom_id"])
        identity = dict(zip(REQUIRED_COLUMNS, REQUIRED_COLUMNS))
        cases = [
            ({key: value for key, value in identity.items() if key != "field"}, "each required field"),
            ({**identity, "field": None}, "each required field"),
            ({**identity, "field": "unknown"}, "were not found"),
            ({**identity, "field": "value"}, "only once"),
            ({**identity, "bogus": "custom_id"}, "Unknown required-field"),
            ({**identity, "record_id": "custom_id"}, "conflict with columns retained"),
        ]
        for mapping, message in cases:
            with self.subTest(mapping=mapping):
                with self.assertRaisesRegex(ValueError, message):
                    map_columns(frame, mapping)
        with self.assertRaisesRegex(ValueError, "column mapping"):
            map_columns(frame, [])

    def test_header_and_size_validation_applies_before_mapping(self):
        with self.assertRaisesRegex(ValueError, "DataFrame"):
            suggest_mapping([])
        with self.assertRaisesRegex(ValueError, "Duplicate column"):
            suggest_mapping(pd.DataFrame(columns=["field", " field "]))
        with self.assertRaisesRegex(ValueError, "10,000"):
            suggest_mapping(pd.DataFrame(index=range(10_001)))
        with self.assertRaisesRegex(ValueError, "50"):
            suggest_mapping(pd.DataFrame(columns=range(51)))


if __name__ == "__main__":
    unittest.main()
