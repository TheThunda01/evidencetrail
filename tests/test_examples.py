"""Keep the public demonstration's promises tied to exact expected findings."""

import json
from pathlib import Path
import unittest

from evidencetrail.audit import audit_table
from evidencetrail.io import load_table

ROOT = Path(__file__).resolve().parents[1]


class ExampleTests(unittest.TestCase):
    def test_demo_matches_five_documented_findings(self):
        content = (ROOT / "examples/demo_records.csv").read_bytes()
        result = audit_table(load_table("demo_records.csv", content))
        expected = json.loads((ROOT / "examples/expected_findings.json").read_text())
        actual = [{"code": f.code, "row_numbers": list(f.row_numbers)} for f in result.findings]
        self.assertEqual(actual, expected)
        self.assertEqual(result.records_count, 20)
        self.assertEqual(result.report_count, 5)

    def test_clean_example_has_no_findings(self):
        result = audit_table(load_table("clean_records.csv", (ROOT / "examples/clean_records.csv").read_bytes()))
        self.assertEqual(result.findings, [])

    def test_excel_sheets_match_csv_examples(self):
        content = (ROOT / "examples/demo_records.xlsx").read_bytes()
        for sheet, filename in [("Demo", "demo_records.csv"), ("Clean", "clean_records.csv")]:
            with self.subTest(sheet=sheet):
                actual = load_table("demo_records.xlsx", content, sheet_name=sheet)
                expected = load_table(filename, (ROOT / "examples" / filename).read_bytes())
                self.assertTrue(actual.equals(expected))


if __name__ == "__main__":
    unittest.main()
