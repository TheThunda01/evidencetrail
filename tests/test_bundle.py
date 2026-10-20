"""Check reproducibility and content boundaries in the downloadable audit."""

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import unittest
from zipfile import ZipFile

from evidencetrail import __version__
from evidencetrail.audit import audit_table
from evidencetrail.comparison import compare_tables
from evidencetrail.io import load_table
from evidencetrail.progress import evidence_completeness, review_progress
from evidencetrail.reports import audit_bundle
from evidencetrail.bundle import verify_bundle

ROOT = Path(__file__).resolve().parents[1]


class BundleTests(unittest.TestCase):
    def test_manifest_and_reports_match_selected_input(self):
        content = (ROOT / "examples/demo_records.csv").read_bytes()
        frame = load_table("demo.csv", content)
        source = {"filename": "demo.csv", "sha256": sha256(content).hexdigest(), "worksheet": None,
                  "column_mapping": {"record_id": "Row ID"}}
        data = audit_bundle(audit_table(frame), source, review_progress(frame), evidence_completeness(frame))
        self.assertTrue(verify_bundle(data)["consistent"])
        with ZipFile(BytesIO(data)) as archive:
            self.assertEqual(set(archive.namelist()), {"audit-summary.md", "findings.csv", "source-manifest.json", "review-progress.json", "field-completeness.csv", "artifact-manifest.json"})
            manifest = json.loads(archive.read("source-manifest.json"))
            self.assertEqual(manifest["source"], source)
            self.assertEqual(manifest["version"], __version__)
            self.assertFalse(manifest["original_upload_included"])
            self.assertNotIn(frame.iloc[0]["value"], archive.read("audit-summary.md").decode())
            self.assertEqual(json.loads(archive.read("review-progress.json"))["pending"], 19)

    def test_reviewer_examples_have_documented_differences(self):
        left = load_table("a.csv", (ROOT / "examples/reviewer_a.csv").read_bytes())
        right = load_table("b.csv", (ROOT / "examples/reviewer_b.csv").read_bytes())
        comparison = compare_tables(left, right)
        self.assertEqual(comparison.summary["comparable_pairs"], 19)
        self.assertEqual(comparison.summary["differences"], 2)
        self.assertEqual(comparison.summary["agreements"], 17)
        self.assertEqual(comparison.summary["left_only"], 1)
        self.assertEqual(comparison.summary["right_only"], 1)
        self.assertEqual(int(comparison.pairs["locator_diff"].sum()), 2)


if __name__ == "__main__":
    unittest.main()
