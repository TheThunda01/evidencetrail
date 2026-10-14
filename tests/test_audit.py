"""Checks for audit behavior and boundaries that affect research interpretation."""

import unittest

import pandas as pd

from evidencetrail.audit import (
    CHECKED_RULES,
    FINDING_COLUMNS,
    REQUIRED_COLUMNS,
    audit_table,
)


def record(**updates):
    row = dict(zip(REQUIRED_COLUMNS, (
        "R-001", "P-001", "setting", "National", "Reported", "Page 4", "Pending",
    )))
    row.update(updates)
    return row


class AuditTests(unittest.TestCase):
    def test_clean_table_and_empty_table_have_stable_outputs(self):
        result = audit_table(pd.DataFrame([record()]))
        self.assertEqual(result.findings, [])
        self.assertEqual(result.records_count, 1)
        self.assertEqual(result.report_count, 1)
        self.assertEqual(result.checked_rules, list(CHECKED_RULES))
        self.assertEqual(list(result.to_frame().columns), list(FINDING_COLUMNS))
        empty = audit_table(pd.DataFrame(columns=REQUIRED_COLUMNS))
        self.assertEqual((empty.records_count, empty.report_count), (0, 0))
        self.assertEqual(list(empty.to_frame().columns), list(FINDING_COLUMNS))

    def test_all_rule_types_and_spreadsheet_row_positions(self):
        frame = pd.DataFrame([
            record(record_id="", report_id=" ", field=None,
                   evidence_status="Reported", value="", source_locator=None,
                   review_status="Disagreement"),
            record(record_id="R-002", evidence_status="not reported", review_status="Done"),
        ], index=[99, 23])
        result = audit_table(frame)
        codes = {finding.code for finding in result.findings}
        self.assertEqual(codes, set(CHECKED_RULES) - {"DUPLICATE_RECORD_ID"})
        self.assertEqual({f.row_numbers for f in result.findings if f.code.startswith("INVALID")}, {(3,)})
        self.assertEqual({f.row_numbers for f in result.findings if not f.code.startswith("INVALID")}, {(2,)})
        self.assertTrue(all(f.severity == "review" for f in result.findings
                            if f.code in {"MISSING_REPORTED_VALUE", "MISSING_SOURCE_LOCATOR", "REVIEWER_DISAGREEMENT"}))

    def test_duplicate_id_is_one_finding_per_group(self):
        result = audit_table(pd.DataFrame([
            record(record_id=" R-001 "),
            record(record_id="R-002"),
            record(record_id="R-001", field="sector"),
            record(record_id="R-001"),
            record(record_id="R-002"),
        ]))
        self.assertEqual(len(result.findings), 2)
        self.assertEqual(result.findings[0].row_numbers, (2, 4, 5))
        self.assertEqual(result.findings[1].row_numbers, (3, 6))
        self.assertEqual(result.findings[0].field, "")
        self.assertEqual(result.to_frame().iloc[0]["row_numbers"], "2, 4, 5")

    def test_whitespace_is_ignored_without_mutating_input(self):
        frame = pd.DataFrame([record(evidence_status=" Reported ", value=" NA ",
                                     review_status=" Verified ")])
        frame.columns = [f" {column} " for column in frame.columns]
        before = frame.copy(deep=True)
        self.assertFalse(audit_table(frame).findings)
        pd.testing.assert_frame_equal(frame, before)

    def test_missingness_statuses_remain_distinct_without_inferred_absence(self):
        frame = pd.DataFrame([
            record(record_id="R-001", evidence_status="Not reported", value="", source_locator=""),
            record(record_id="R-002", evidence_status="Unclear", value=None, source_locator=None),
            record(record_id="R-003", evidence_status="Not applicable", value="", source_locator=""),
            record(record_id="R-004", evidence_status="Explicitly absent", value="", source_locator="Page 2"),
        ])
        self.assertFalse(audit_table(frame).findings)
        frame.loc[3, "source_locator"] = ""
        result = audit_table(frame)
        self.assertEqual([f.code for f in result.findings], ["MISSING_SOURCE_LOCATOR"])
        self.assertEqual(result.findings[0].row_numbers, (5,))

    def test_literal_na_and_null_are_values_but_actual_missing_values_are_not(self):
        frame = pd.DataFrame([record(record_id=f"R-{i}", value=value)
                              for i, value in enumerate(["NA", "null", "nan", 0, False, pd.NA, float("nan")])])
        result = audit_table(frame)
        self.assertEqual([f.row_numbers for f in result.findings], [(7,), (8,)])
        self.assertTrue(all(f.code == "MISSING_REPORTED_VALUE" for f in result.findings))

    def test_report_count_is_nonempty_distinct_ids(self):
        result = audit_table(pd.DataFrame([
            record(record_id="R-1", report_id=" P-1 "),
            record(record_id="R-2", report_id="P-1"),
            record(record_id="R-3", report_id="P-2"),
            record(record_id="R-4", report_id=""),
        ]))
        self.assertEqual(result.records_count, 4)
        self.assertEqual(result.report_count, 2)

    def test_schema_and_resource_limits_are_explicit(self):
        with self.assertRaisesRegex(ValueError, "Missing required columns: review_status"):
            audit_table(pd.DataFrame(columns=REQUIRED_COLUMNS[:-1]))
        with self.assertRaisesRegex(ValueError, "Duplicate column headers"):
            audit_table(pd.DataFrame(columns=[*REQUIRED_COLUMNS, " record_id "]))
        with self.assertRaisesRegex(ValueError, "10,000"):
            audit_table(pd.DataFrame([record()] * 10_001))
        with self.assertRaisesRegex(ValueError, "50"):
            audit_table(pd.DataFrame(columns=[f"column-{i}" for i in range(51)]))
        with self.assertRaisesRegex(ValueError, "DataFrame"):
            audit_table([])


if __name__ == "__main__":
    unittest.main()
