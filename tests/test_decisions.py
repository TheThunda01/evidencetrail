"""Decision logs preserve provenance and never manufacture source support."""

import copy
from io import BytesIO
import json
import unittest

import pandas as pd

from evidencetrail.decisions import DECISION_COLUMNS, decisions_csv, decisions_json, make_decision


def pair(**changes):
    record = {"report_id": "P-1", "field": "setting", "left_row": 2, "right_row": 3,
              "left_record_id": "L-1", "right_record_id": "R-1", "left_value": "National", "right_value": "Regional",
              "left_evidence_status": "Reported", "right_evidence_status": "Reported",
              "left_source_locator": "p. 4", "right_source_locator": "p. 5", "status": "Difference",
              "different_fields": "value", "locator_diff": True}
    record.update(changes)
    return record


class DecisionTests(unittest.TestCase):
    def test_selected_reviewer_retains_both_originals_and_explicit_choice(self):
        original = pair()
        before = copy.deepcopy(original)
        result = make_decision(original, "Use second reviewer", " AB ", " Checked Table 2. ", timestamp="2026-10-13T14:00:00-06:00")
        self.assertEqual(original, before)
        self.assertEqual(result["value"], "Regional")
        self.assertEqual(result["source_locator"], "p. 5")
        self.assertEqual(result["left_value"], "National")
        self.assertEqual(result["right_value"], "Regional")
        self.assertEqual(result["status"], "Decision recorded")
        self.assertNotIn("review_status", result)
        self.assertEqual(result["reviewer"], "AB")
        self.assertEqual(result["decided_at"], "2026-10-13T20:00:00Z")
        self.assertEqual(json.loads(result["source_key"]), {"report_id": "P-1", "field": "setting"})
        self.assertEqual(tuple(result), DECISION_COLUMNS)

    def test_defer_requires_person_and_reason_but_no_selected_result(self):
        result = make_decision(pair(left_evidence_status="invalid", left_source_locator=""), "Defer", "AB", "Needs source review.")
        self.assertEqual(result["status"], "Deferred")
        self.assertEqual([result[column] for column in ("value", "evidence_status", "source_locator")], ["", "", ""])
        self.assertTrue(result["decided_at"].endswith("Z"))
        for reviewer, rationale in (("", "reason"), ("AB", " ")):
            with self.assertRaisesRegex(ValueError, "reviewer name"):
                make_decision(pair(), "Defer", reviewer, rationale)

    def test_custom_value_keeps_distinct_missingness_statuses(self):
        for status in ("Not reported", "Unclear", "Not applicable"):
            decision = make_decision(pair(), "Enter a different value", "AB", "Rechecked source.", custom_evidence_status=status)
            self.assertEqual(decision["evidence_status"], status)
            self.assertEqual(decision["source_locator"], "")
        result = make_decision(pair(), "Enter a different value", "AB", "The source explicitly states absence.",
                               custom_evidence_status="Explicitly absent", custom_source_locator="p. 6")
        self.assertEqual(result["value"], "")

    def test_inherited_or_custom_results_need_required_evidence_metadata(self):
        cases = [(pair(left_value=""), "Use first reviewer", {}, "needs a value"),
                 (pair(right_source_locator=""), "Use second reviewer", {}, "needs a source locator"),
                 (pair(left_evidence_status="invalid"), "Use first reviewer", {}, "recognized evidence status"),
                 (pair(), "Enter a different value", {"custom_value": "x", "custom_evidence_status": "Reported"}, "needs a source locator"),
                 (pair(), "Enter a different value", {"custom_evidence_status": "Explicitly absent"}, "needs a source locator")]
        for record, choice, changes, message in cases:
            with self.subTest(choice=choice, changes=changes):
                with self.assertRaisesRegex(ValueError, message):
                    make_decision(record, choice, "AB", "Source reviewed.", **changes)

    def test_unmatched_blocked_or_incomplete_records_cannot_be_decided(self):
        for status in ("Left only", "Right only", "Blocked", ""):
            with self.assertRaisesRegex(ValueError, "matched pair"):
                make_decision(pair(status=status), "Defer", "AB", "reason")
        with self.assertRaisesRegex(ValueError, "both reviewers"):
            make_decision(pair(right_row=pd.NA), "Defer", "AB", "reason")
        incomplete = pair()
        del incomplete["left_value"]
        with self.assertRaisesRegex(ValueError, "missing left_value"):
            make_decision(incomplete, "Defer", "AB", "reason")

    def test_source_metadata_agreement_is_not_verification(self):
        result = make_decision(pair(status="Agreement", right_value="National"), "Use first reviewer", "AB", "Accepted for project review.")
        self.assertEqual(result["comparison_status"], "Agreement")
        self.assertEqual(result["status"], "Decision recorded")
        self.assertNotIn("Verified", result.values())

    def test_csv_escapes_formulas_but_json_preserves_original_text(self):
        decision = make_decision(pair(left_value="=1+1"), "Use first reviewer", "@name", "+reason", timestamp="2026-10-14T00:00:00Z")
        frame = pd.read_csv(BytesIO(decisions_csv([decision])), keep_default_na=False)
        self.assertEqual(frame.iloc[0]["value"], "'=1+1")
        self.assertEqual(frame.iloc[0]["reviewer"], "'@name")
        self.assertEqual(frame.iloc[0]["rationale"], "'+reason")
        provenance = {"comparison_id": "digest", "sources": ["left.csv", "right.csv"]}
        exported = json.loads(decisions_json([decision], provenance))
        self.assertEqual(exported["decisions"][0]["value"], "=1+1")
        self.assertEqual(exported["provenance"], provenance)
        self.assertEqual(list(pd.read_csv(BytesIO(decisions_csv([]))).columns), list(DECISION_COLUMNS))

    def test_timestamp_requires_explicit_timezone(self):
        for timestamp in ("2026-10-13T14:00:00", "yesterday"):
            with self.assertRaisesRegex(ValueError, "timezone"):
                make_decision(pair(), "Defer", "AB", "reason", timestamp=timestamp)


if __name__ == "__main__":
    unittest.main()
