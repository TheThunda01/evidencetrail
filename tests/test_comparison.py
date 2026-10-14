"""Reviewer matching must remain explicit and conservative about ambiguity."""

import unittest

import pandas as pd

from evidencetrail.comparison import compare_tables, comparison_id


def row(**changes):
    record = {"record_id": "L-1", "report_id": "P-1", "field": "setting",
              "value": "National", "evidence_status": "Reported", "source_locator": "p. 4"}
    record.update(changes)
    return record


class ComparisonTests(unittest.TestCase):
    def test_matching_is_case_sensitive_and_trims_only_outer_whitespace(self):
        first = pd.DataFrame([row(value=" National "), row(record_id="L-2", report_id="P-2", value="A  B"),
                              row(record_id="L-3", report_id="P-3", value="National")])
        second = pd.DataFrame([row(record_id="R-1", value="National"), row(record_id="R-2", report_id="P-2", value="A B"),
                               row(record_id="R-3", report_id="P-3", value="national")])
        result = compare_tables(first, second)
        self.assertEqual(result.pairs.status.tolist(), ["Agreement", "Difference", "Difference"])
        self.assertEqual(result.pairs.different_fields.tolist(), ["", "value", "value"])
        self.assertEqual(result.summary, {"comparable_pairs": 3, "agreements": 1, "differences": 2,
                                          "left_only": 0, "right_only": 0, "blocked_rows": 0})

    def test_source_only_difference_is_separate_from_field_agreement(self):
        result = compare_tables(pd.DataFrame([row()]), pd.DataFrame([row(source_locator="Table 2")]))
        self.assertEqual(result.pairs.iloc[0]["status"], "Agreement")
        self.assertTrue(result.pairs.iloc[0]["locator_diff"])
        self.assertEqual(result.pairs.iloc[0]["different_fields"], "")

    def test_duplicate_groups_block_every_row_and_unique_counterpart(self):
        left = pd.DataFrame([row(), row(record_id="L-2"), row(record_id="L-3", report_id="P-2")])
        right = pd.DataFrame([row(record_id="R-1"), row(record_id="R-2", report_id="P-3")])
        result = compare_tables(left, right)
        self.assertEqual(result.summary["blocked_rows"], 3)
        self.assertEqual(result.pairs.status.tolist(), ["Left only", "Right only"])
        self.assertEqual(result.issues.reason.tolist(), ["Duplicate key", "Counterpart has duplicate key"])
        self.assertEqual(result.issues.row_numbers.tolist(), ["2, 3", "2"])

    def test_duplicate_groups_on_both_sides_never_cross_join(self):
        table = pd.DataFrame([row(), row(record_id="L-2")])
        result = compare_tables(table, table)
        self.assertTrue(result.pairs.empty)
        self.assertEqual(result.summary["blocked_rows"], 4)
        self.assertEqual(result.issues.reason.tolist(), ["Duplicate key", "Duplicate key"])

    def test_missing_keys_are_blocked_and_rows_use_spreadsheet_positions(self):
        left = pd.DataFrame([row(report_id=pd.NA), row(field=" "), row(report_id="P-2")], index=[200, 100, 50])
        right = pd.DataFrame([row(report_id="P-2")], index=[101])
        result = compare_tables(left, right)
        self.assertEqual(result.summary["blocked_rows"], 2)
        self.assertEqual(result.issues.row_numbers.tolist(), ["2", "3"])
        self.assertEqual(result.pairs.left_row.tolist(), [4])
        self.assertEqual(result.pairs.right_row.tolist(), [2])

    def test_unicode_and_delimiters_do_not_collapse_distinct_keys(self):
        first = pd.DataFrame([row(report_id="a|b", field="c", value="ñ"),
                              row(record_id="L-2", report_id="a", field="b|c", value="測定")])
        second = pd.DataFrame([row(report_id="a", field="b|c", value="測定"),
                               row(record_id="R-2", report_id="a|b", field="c", value="ñ")])
        result = compare_tables(first, second)
        self.assertEqual(result.summary["agreements"], 2)
        self.assertEqual(result.pairs.right_row.tolist(), [3, 2])

    def test_missing_values_and_evidence_statuses_are_not_inferred(self):
        first = pd.DataFrame([row(value=None, evidence_status="Not reported"),
                              row(record_id="L-2", report_id="P-2", value=0),
                              row(record_id="L-3", report_id="P-3", value="NA")])
        second = pd.DataFrame([row(value=pd.NA, evidence_status="Explicitly absent"),
                               row(record_id="R-2", report_id="P-2", value="0"),
                               row(record_id="R-3", report_id="P-3", value=None)])
        result = compare_tables(first, second)
        self.assertEqual(result.pairs.status.tolist(), ["Difference", "Agreement", "Difference"])
        self.assertEqual(result.pairs.different_fields.tolist(), ["evidence_status", "", "value"])

    def test_inputs_and_result_copies_are_independent(self):
        left = pd.DataFrame([row(value=" National ")])
        right = pd.DataFrame([row(record_id="R-1")])
        left.columns = [f" {column} " for column in left.columns]
        before_left, before_right = left.copy(deep=True), right.copy(deep=True)
        result = compare_tables(left, right)
        result_copy = result.to_frame()
        result_copy.loc[0, "left_value"] = "changed"
        pd.testing.assert_frame_equal(left, before_left)
        pd.testing.assert_frame_equal(right, before_right)
        self.assertEqual(result.pairs.iloc[0]["left_value"], "National")

    def test_empty_and_unmatched_outputs_have_stable_schema(self):
        empty = pd.DataFrame(columns=row().keys())
        result = compare_tables(empty, empty)
        self.assertEqual(list(result.pairs.columns), ["report_id", "field", "left_row", "right_row",
            "left_record_id", "right_record_id", "left_value", "right_value", "left_evidence_status",
            "right_evidence_status", "left_source_locator", "right_source_locator", "status", "different_fields", "locator_diff"])
        self.assertEqual(result.summary["comparable_pairs"], 0)
        unmatched = compare_tables(pd.DataFrame([row()]), empty)
        self.assertEqual(unmatched.pairs.iloc[0]["status"], "Left only")
        self.assertTrue(pd.isna(unmatched.pairs.iloc[0]["right_row"]))

    def test_required_schema_and_custom_keys(self):
        table = pd.DataFrame([row()])
        with self.assertRaisesRegex(ValueError, "source_locator"):
            compare_tables(table.drop(columns=["source_locator"]), table)
        with self.assertRaisesRegex(ValueError, "Duplicate column headers"):
            compare_tables(pd.DataFrame(columns=[*table.columns, " report_id "]), table)
        with self.assertRaisesRegex(ValueError, "nonempty"):
            compare_tables(table, table, key_columns=())
        result = compare_tables(table, table, key_columns=("record_id",))
        self.assertEqual(result.summary["agreements"], 1)

    def test_comparison_id_binds_every_input_and_canonicalizes_mapping_order(self):
        args = dict(left_sha="a" * 64, right_sha="b" * 64, left_sheet="Sheet 1", right_sheet="Sheet 2",
                    left_mapping={"value": "Value", "field": "Question"}, right_mapping={"value": "Answer"})
        baseline = comparison_id(**args)
        self.assertEqual(len(baseline), 64)
        self.assertEqual(baseline, comparison_id(**dict(args, left_mapping={"field": "Question", "value": "Value"})))
        for changed in ({"left_sha": "c" * 64}, {"right_sha": "d" * 64}, {"left_sheet": "Other"},
                        {"right_sheet": None}, {"left_mapping": {}}, {"right_mapping": {}}, {"key_columns": ["record_id"]}):
            self.assertNotEqual(baseline, comparison_id(**dict(args, **changed)))


if __name__ == "__main__":
    unittest.main()
