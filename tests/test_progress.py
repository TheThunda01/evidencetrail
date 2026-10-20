"""Descriptive status counts are distinct from structural or scientific validity."""

import json
import unittest

import pandas as pd

from evidencetrail.audit import REQUIRED_COLUMNS, audit_table
from evidencetrail.progress import COMPLETENESS_COLUMNS, evidence_completeness, review_progress


class ProgressTests(unittest.TestCase):
    def test_pending_rows_can_have_no_findings_but_remain_visible(self):
        frame = pd.DataFrame([
            ["R1", "P1", "setting", "National", "Reported", "p1", "Pending"],
            ["R2", "P2", "setting", "Regional", "Reported", "p2", " Pending "],
        ], columns=REQUIRED_COLUMNS)
        self.assertFalse(audit_table(frame).findings)
        self.assertEqual(review_progress(frame), {
            "records": 2, "pending": 2, "verified": 0, "disagreement": 0, "invalid": 0,
        })

    def test_all_recorded_states_include_blanks_and_unrecognized_labels(self):
        frame = pd.DataFrame({" review_status ": [
            "Pending", " Verified ", "Disagreement", "verified", "", None, pd.NA,
        ]})
        original = frame.copy(deep=True)
        result = review_progress(frame)
        self.assertEqual(result, {
            "records": 7, "pending": 1, "verified": 1, "disagreement": 1, "invalid": 4,
        })
        self.assertEqual(sum(result[key] for key in result if key != "records"), result["records"])
        pd.testing.assert_frame_equal(frame, original)

    def test_locator_coverage_has_status_specific_denominator(self):
        frame = pd.DataFrame([
            ["setting", "Reported", "National", "Page 2"],
            ["setting", "Explicitly absent", "", ""],
            ["setting", "Not reported", "", ""],
            ["setting", "Not applicable", "", ""],
            ["setting", "Unclear", "", ""],
            ["other", "Not applicable", "", ""],
            ["invalid", "reported", "National", "Page 3"],
        ], columns=["field", "evidence_status", "value", "source_locator"])
        result = evidence_completeness(frame).to_dict("records")
        first, other, invalid = result
        self.assertEqual((first["records"], first["source_locator_required"], first["source_locator_provided"]), (5, 2, 1))
        self.assertEqual(first["source_locator_coverage"], 0.5)
        self.assertEqual((first["not_reported"], first["not_applicable"], first["unclear"]), (1, 1, 1))
        self.assertIsNone(other["source_locator_coverage"])
        self.assertIsNone(invalid["source_locator_coverage"])
        # Literal strings and optional blanks are never relabeled as truth/absence.
        self.assertEqual(other["missing_reported_value"], 0)
        json.dumps(result, allow_nan=False)

    def test_evidence_totals_and_required_metadata_match_audit_semantics(self):
        frame = pd.DataFrame([
            [" first ", " Reported ", " NA ", " page 1 "],
            ["first", "Reported", None, ""],
            ["second", "Explicitly absent", "", None],
            ["second", "Not reported", "", ""],
            ["second", "Unclear", "", ""],
            ["second", "Not applicable", "", ""],
            [None, "reported", "text", "p1"],
        ], columns=["field", "evidence_status", "value", "source_locator"])
        original = frame.copy(deep=True)
        result = evidence_completeness(frame)
        self.assertEqual(result.columns.tolist(), list(COMPLETENESS_COLUMNS))
        self.assertEqual(result["field"].tolist(), ["first", "second", ""])
        first, second, invalid = result.to_dict("records")
        self.assertEqual((first["records"], first["reported"], first["missing_reported_value"],
                          first["missing_source_locator"]), (2, 2, 1, 1))
        self.assertEqual((second["records"], second["explicitly_absent"], second["not_reported"],
                          second["unclear"], second["not_applicable"], second["missing_source_locator"]),
                         (4, 1, 1, 1, 1, 1))
        self.assertEqual((invalid["records"], invalid["invalid_evidence_status"]), (1, 1))
        pd.testing.assert_frame_equal(frame, original)

    def test_empty_summaries_and_validation(self):
        self.assertEqual(review_progress(pd.DataFrame(columns=["review_status"])), {
            "records": 0, "pending": 0, "verified": 0, "disagreement": 0, "invalid": 0,
        })
        empty = evidence_completeness(pd.DataFrame(columns=REQUIRED_COLUMNS))
        self.assertTrue(empty.empty)
        self.assertEqual(empty.columns.tolist(), list(COMPLETENESS_COLUMNS))
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            evidence_completeness(pd.DataFrame(columns=["field"]))
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            review_progress(pd.DataFrame())
        with self.assertRaisesRegex(ValueError, "Duplicate column"):
            review_progress(pd.DataFrame(columns=["review_status", " review_status "]))
        with self.assertRaisesRegex(ValueError, "10,000"):
            review_progress(pd.DataFrame({"review_status": ["Pending"] * 10_001}))


if __name__ == "__main__":
    unittest.main()
