"""Reviewer matching must remain explicit and conservative about ambiguity."""

import json
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

    def test_coverage_keeps_blocked_and_unmatched_rows_in_denominator(self):
        left = pd.DataFrame([row(report_id="P-1"), row(report_id="P-2"),
                             row(report_id="P-3"), row(report_id="P-3")])
        right = pd.DataFrame([row(report_id="P-1"), row(report_id="P-3")])
        result = compare_tables(left, right)
        first, second = result.metrics["pairing"]
        self.assertEqual((first["input_rows"], first["matched_rows"], first["unmatched_rows"], first["blocked_rows"]), (4, 1, 1, 2))
        self.assertEqual((second["input_rows"], second["matched_rows"], second["unmatched_rows"], second["blocked_rows"]), (2, 1, 0, 1))
        self.assertEqual(first["coverage_fraction"], 0.25)
        self.assertEqual(second["coverage_fraction"], 0.5)
        for side in (first, second):
            self.assertEqual(side["input_rows"], side["matched_rows"] + side["unmatched_rows"] + side["blocked_rows"])

    def test_blank_pairs_are_separate_from_nonblank_agreement(self):
        left = pd.DataFrame([row(report_id="P1", value=" National "),
            row(report_id="P2", value=" ", evidence_status="Not reported"),
            row(report_id="P3", value=None), row(report_id="P4", value="NA")])
        right = pd.DataFrame([row(report_id="P1", value="National"),
            row(report_id="P2", value=None, evidence_status="Not reported"),
            row(report_id="P3", value="National"), row(report_id="P4", value="")])
        result = compare_tables(left, right)
        value, status = result.metrics["fields"]
        self.assertEqual(value, {"field": "value", "matched_pairs": 4, "both_nonblank": 1,
            "exact_matches_both_nonblank": 1, "agreement_fraction_both_nonblank": 1.0,
            "left_blank_only": 1, "right_blank_only": 1, "both_blank": 1})
        self.assertEqual(status["both_nonblank"], 4)
        self.assertEqual(status["exact_matches_both_nonblank"], 4)
        self.assertEqual(result.metrics["raw_exact_pair_agreement"],
                         {"exact_matches": 2, "matched_pairs": 4, "fraction": 0.5})
        # Literal NA is text, not inferred missingness; no input is rewritten.
        self.assertEqual(left.loc[3, "value"], "NA")

    def test_no_eligible_values_or_empty_tables_have_undefined_rates(self):
        blank = pd.DataFrame([row(value="", evidence_status="Not reported")])
        result = compare_tables(blank, blank)
        self.assertEqual(result.summary["agreements"], 1)
        self.assertIsNone(result.metrics["fields"][0]["agreement_fraction_both_nonblank"])
        empty = pd.DataFrame(columns=row().keys())
        result = compare_tables(empty, empty)
        self.assertTrue(all(item["coverage_fraction"] is None for item in result.metrics["pairing"]))
        self.assertTrue(all(item["agreement_fraction_both_nonblank"] is None for item in result.metrics["fields"]))
        self.assertIsNone(result.metrics["raw_exact_pair_agreement"]["fraction"])
        json_text = json.dumps(result.metrics, allow_nan=False)
        self.assertIn("null", json_text)

    def test_metric_fields_follow_custom_comparison_contract(self):
        table = pd.DataFrame([row()])
        result = compare_tables(table, table, compare_columns=("evidence_status",))
        self.assertEqual([item["field"] for item in result.metrics["fields"]], ["evidence_status"])

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
