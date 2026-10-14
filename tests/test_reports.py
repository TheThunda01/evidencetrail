"""Report accuracy, omitted source content, and spreadsheet-export safety."""

import csv
from io import StringIO
import unittest

import pandas as pd

from evidencetrail import __version__
from evidencetrail.audit import CHECKED_RULES, FINDING_COLUMNS, AuditResult, Finding, REQUIRED_COLUMNS, audit_table
from evidencetrail.reports import findings_csv, report_markdown, spreadsheet_safe_frame


class ReportTests(unittest.TestCase):
    def test_clean_csv_keeps_header_and_unicode_bom(self):
        result = audit_table(pd.DataFrame(columns=REQUIRED_COLUMNS))
        output = findings_csv(result)
        self.assertTrue(output.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(list(csv.reader(StringIO(output.decode("utf-8-sig")))), [list(FINDING_COLUMNS)])

    def test_formula_like_identifiers_are_escaped_in_export(self):
        formulas = ["=SUM(1,2)", "+1+1", "-1+1", "@SUM(1,2)", "\t =1+1", "\r\n@A1"]
        findings = [Finding("MISSING_REPORT_ID", "error", (i + 2,), text, "plain", "message", "suggestion")
                    for i, text in enumerate(formulas)]
        result = AuditResult(findings, len(formulas), 0, list(CHECKED_RULES))
        rows = list(csv.DictReader(StringIO(findings_csv(result).decode("utf-8-sig"))))
        self.assertEqual([row["record_id"] for row in rows], ["'" + text for text in formulas])
        self.assertTrue(all(row["field"] == "plain" for row in rows))
        self.assertEqual(result.findings[0].record_id, formulas[0])

    def test_safe_preview_escapes_strings_and_headers_without_changing_source(self):
        frame = pd.DataFrame({
            "=formula_header": ["=SUM(1,2)", "\t @A1", "plain"],
            "'=formula_header": ["+cmd", "-cmd", "@cmd"],
            "count": pd.Series([-3, 0, pd.NA], dtype="Int64"),
            "ratio": [1.5, float("nan"), -2.0],
        })
        frame.columns.name = "fields"
        original = frame.copy(deep=True)
        safe = spreadsheet_safe_frame(frame)
        pd.testing.assert_frame_equal(frame, original)
        self.assertEqual(safe.columns.tolist(), ["'=formula_header", "'=formula_header [2]", "count", "ratio"])
        self.assertEqual(safe.columns.name, "fields")
        self.assertEqual(safe.iloc[:, 0].tolist(), ["'=SUM(1,2)", "'\t @A1", "plain"])
        self.assertEqual(safe.iloc[:, 1].tolist(), ["'+cmd", "'-cmd", "'@cmd"])
        pd.testing.assert_series_equal(safe["count"], frame["count"])
        pd.testing.assert_series_equal(safe["ratio"], frame["ratio"])
        self.assertTrue(safe.columns.is_unique)

    def test_safe_preview_retains_clean_empty_frames(self):
        frame = pd.DataFrame(columns=["record_id", "value"])
        pd.testing.assert_frame_equal(spreadsheet_safe_frame(frame), frame)

    def test_summary_counts_duplicate_groups_once_and_affected_rows_separately(self):
        frame = pd.DataFrame([
            ["SECRET-ID", "P-1", "SECRET-FIELD", "SECRET-VALUE", "Reported", "Page 1", "Pending"],
            ["SECRET-ID", "P-1", "SECRET-FIELD", "SECRET-VALUE", "Reported", "Page 2", "Pending"],
        ], columns=REQUIRED_COLUMNS)
        result = audit_table(frame)
        report = report_markdown(result, "example.csv", "a" * 64)
        self.assertIn("Findings: 1", report)
        self.assertIn("Records with findings: 2", report)
        self.assertIn("Distinct nonempty report IDs: 1", report)
        self.assertIn("`DUPLICATE_RECORD_ID` | 1", report)
        self.assertIn("does not certify the extraction", report)
        self.assertNotIn("SECRET", report)

    def test_filename_is_escaped_and_digest_is_validated(self):
        result = AuditResult([], 0, 0, list(CHECKED_RULES))
        report = report_markdown(result, "[link](https://example.test)\n<script>bad</script>.csv", "F" * 64)
        self.assertIn(r"\[link\]\(https://example", report)
        self.assertNotIn("<script>", report)
        self.assertIn("&lt;script&gt;", report)
        self.assertIn("`" + "f" * 64 + "`", report)
        with self.assertRaisesRegex(ValueError, "64-character"):
            report_markdown(result, "file.csv", "invalid")

    def test_report_records_app_version_and_selected_worksheet(self):
        result = AuditResult([], 0, 0, list(CHECKED_RULES))
        report = report_markdown(result, "file.xlsx", "a" * 64, sheet_name="Extraction [final]")
        self.assertIn(f"EvidenceTrail version: `{__version__}`", report)
        self.assertIn(r"Selected worksheet: Extraction \[final\]", report)
        self.assertNotIn("Selected worksheet:", report_markdown(result, "file.csv", "a" * 64))


if __name__ == "__main__":
    unittest.main()
