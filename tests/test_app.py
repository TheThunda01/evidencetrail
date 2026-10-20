"""Exercise public workflows, session boundaries, and traceable exports."""

import csv
from io import StringIO
import json
from pathlib import Path
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

from evidencetrail.audit import REQUIRED_COLUMNS
from evidencetrail.comparison import compare_tables
from evidencetrail.decisions import make_decision
from evidencetrail.io import load_table
from evidencetrail.ui import Source, decision_csv_with_provenance

ROOT = Path(__file__).resolve().parents[1]


def prefixed(elements, prefix):
    return next(element for element in elements if element.key and element.key.startswith(prefix))


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)

    def compare(self):
        self.app.run()
        self.app.radio(key="workspace").set_value("Compare reviewers").run()
        self.assertEqual(len(self.app.exception), 0)

    def save_decision(self):
        prefixed(self.app.text_input, "reviewer_").set_value("Reviewer C")
        prefixed(self.app.text_area, "rationale_").set_value("Checked against the cited source.")
        prefixed(self.app.button, "save_").click().run()

    def test_demo_and_clean_example_separate_findings_from_pending_review(self):
        self.app.run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual([m.value for m in self.app.metric], ["20", "5", "2", "3", "19", "0", "1", "0"])
        self.app.radio(key="source_mode").set_value("Clean example").run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual([m.value for m in self.app.metric], ["20", "5", "0", "0", "20", "0", "0", "0"])
        self.assertTrue(any("20 rows are still marked Pending" in item.value for item in self.app.info))
        self.assertTrue(any("scientific accuracy" in item.value for item in self.app.info))
        self.assertEqual(len(self.app.success), 0)
        self.assertEqual([tab.label for tab in self.app.tabs], ["Findings", "By field", "Records", "How it works"])

    def test_filters_search_without_changing_full_audit(self):
        self.app.run()
        self.app.selectbox(key="finding_severity").set_value("Data errors").run()
        self.assertEqual(len(self.app.dataframe[0].value), 2)
        self.app.text_input(key="finding_search").set_value("INVALID").run()
        self.assertEqual(len(self.app.dataframe[0].value), 1)
        self.assertEqual([m.value for m in self.app.metric[:4]], ["20", "5", "2", "3"])

    def test_upload_empty_state_has_no_stale_audit(self):
        self.app.run()
        self.app.radio(key="source_mode").set_value("Upload a file").run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.metric), 0)
        self.assertTrue(any("Choose a CSV or Excel file" in item.value for item in self.app.info))

    def test_conflicting_column_mapping_stops_audit_with_friendly_error(self):
        self.app.run()
        widget = next(box for box in self.app.selectbox if box.key.endswith("_record_id"))
        widget.set_value("report_id").run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.metric), 0)
        self.assertIn("only once", self.app.error[0].value)
        widget = next(box for box in self.app.selectbox if box.key.endswith("_record_id"))
        widget.set_value("record_id").run()
        self.assertEqual([m.value for m in self.app.metric[:4]], ["20", "5", "2", "3"])

    def test_comparison_demo_counts_and_filters(self):
        self.compare()
        self.assertEqual([m.value for m in self.app.metric], ["19", "17", "2", "2"])
        self.assertEqual(len(self.app.dataframe[0].value), 2)
        self.app.selectbox(key="comparison_filter").set_value("All records").run()
        self.assertEqual(len(self.app.dataframe[0].value), 21)
        self.app.selectbox(key="comparison_filter").set_value("Unmatched records").run()
        self.assertEqual(len(self.app.dataframe[0].value), 2)
        self.app.selectbox(key="comparison_filter").set_value("Source-location differences").run()
        self.assertEqual(len(self.app.dataframe[0].value), 2)
        self.assertEqual(len(self.app.exception), 0)

    def test_comparison_metrics_show_explicit_denominators_and_download(self):
        self.compare()
        coverage = self.app.dataframe[1].value
        self.assertEqual(coverage["Matched / submitted"].tolist(), ["19 / 20", "19 / 20"])
        self.assertEqual(coverage["Coverage"].tolist(), ["95.0%", "95.0%"])
        agreement = self.app.dataframe[2].value
        self.assertEqual(agreement["Compared field"].tolist(), ["value", "evidence_status"])
        self.assertTrue(any(item.label == "Download comparison metrics JSON" for item in self.app.get("download_button")))

    def test_field_summary_exposes_denominators_and_download(self):
        self.app.run()
        self.assertEqual(len(self.app.exception), 0)
        summary=self.app.dataframe[1].value
        self.assertIn("source_locator_required",summary.columns)
        self.assertIn("source_locator_provided",summary.columns)
        self.assertIn("source_locator_coverage",summary.columns)
        self.assertTrue(any(item.label == "Download field completeness CSV" for item in self.app.get("download_button")))

    def test_decision_requires_reason_and_replaces_current_pair_entry(self):
        self.compare()
        prefixed(self.app.button, "save_").click().run()
        self.assertIn("reviewer name or identifier and a rationale", self.app.error[0].value)
        self.assertEqual(self.app.session_state["decision_log"], {})
        self.save_decision()
        self.assertEqual(len(self.app.exception), 0)
        records = list(self.app.session_state["decision_log"].values())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "Decision recorded")
        self.assertEqual(records[0]["reviewer"], "Reviewer C")
        prefixed(self.app.selectbox, "choice_").set_value("Defer").run()
        prefixed(self.app.text_area, "rationale_").set_value("Needs a second source check.")
        prefixed(self.app.button, "save_").click().run()
        records = list(self.app.session_state["decision_log"].values())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "Deferred")
        self.assertEqual(records[0]["value"], "")
        self.assertTrue(any("replaces its entry" in item.value for item in self.app.info))

    def test_custom_decision_controls_render_and_validate_required_source_location(self):
        self.compare()
        prefixed(self.app.selectbox, "choice_").set_value("Enter a different value").run()
        prefixed(self.app.text_input, "reviewer_").set_value("Reviewer C")
        prefixed(self.app.text_area, "rationale_").set_value("Resolved from source.")
        prefixed(self.app.text_area, "value_").set_value("Monthly")
        prefixed(self.app.button, "save_").click().run()
        self.assertIn("needs a source locator", self.app.error[0].value)
        prefixed(self.app.text_input, "locator_").set_value("Methods, p. 3")
        prefixed(self.app.button, "save_").click().run()
        record = next(iter(self.app.session_state["decision_log"].values()))
        self.assertEqual((record["value"], record["evidence_status"], record["source_locator"]), ("Monthly", "Reported", "Methods, p. 3"))

    def test_changed_mapping_resets_decisions_for_a_different_comparison(self):
        self.compare()
        self.save_decision()
        identity = self.app.session_state["active_comparison"]
        value = next(box for box in self.app.selectbox if box.key.startswith("first_map_") and box.key.endswith("_value"))
        locator = next(box for box in self.app.selectbox if box.key.startswith("first_map_") and box.key.endswith("_source_locator"))
        value.set_value("source_locator")
        locator.set_value("value")
        self.app.run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertNotEqual(self.app.session_state["active_comparison"], identity)
        self.assertEqual(self.app.session_state["decision_log"], {})

    def test_clear_session_discards_log_and_changes_upload_identity(self):
        self.compare()
        self.save_decision()
        self.app.session_state["private_marker"] = "discard this"
        self.app.button(key="clear_session").click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertNotIn("private_marker", self.app.session_state)
        self.assertEqual(self.app.session_state["_upload_generation"], 1)
        self.assertNotIn("decision_log", self.app.session_state)
        self.assertEqual(self.app.radio(key="workspace").value, "Audit a table")

    def test_source_loader_requires_explicit_mapping_and_keeps_original_values(self):
        content = "ID,Report,Question,Answer,Evidence,Location,Review\n001,P1,setting, NA ,Reported,Page 1,Pending\n"
        script = f'''
from types import SimpleNamespace
from unittest.mock import patch
import streamlit as st
from evidencetrail.ui import load_source
content = {content.encode()!r}
with patch("evidencetrail.ui.st.file_uploader", return_value=SimpleNamespace(name="custom.csv", getvalue=lambda: content)):
    source = load_source("custom")
if source is not None:
    st.dataframe(source.frame)
'''
        app = AppTest.from_string(script).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.dataframe), 0)
        names = ["ID", "Report", "Question", "Answer", "Evidence", "Location", "Review"]
        for box, name in zip(app.selectbox, names):
            box.set_value(name)
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.dataframe[0].value["record_id"].tolist(), ["001"])
        self.assertEqual(app.dataframe[0].value["value"].tolist(), [" NA "])


class SourceExportTests(unittest.TestCase):
    def test_metadata_is_independent_and_decision_csv_contains_provenance(self):
        first_data = (ROOT / "examples/reviewer_a.csv").read_bytes()
        second_data = (ROOT / "examples/reviewer_b.csv").read_bytes()
        first_frame = load_table("first.csv", first_data)
        second_frame = load_table("second.csv", second_data)
        mapping = dict(zip(REQUIRED_COLUMNS, REQUIRED_COLUMNS))
        first = Source(first_frame, "=formula-name.csv", "a" * 64, "Sheet A", mapping)
        second = Source(second_frame, "second.csv", "b" * 64, None, mapping)
        metadata = first.metadata()
        metadata["column_mapping"]["value"] = "changed"
        self.assertEqual(first.mapping["value"], "value")
        pair = compare_tables(first_frame, second_frame).pairs.iloc[0].to_dict()
        decision = make_decision(pair, "Use first reviewer", "Reviewer C", "Checked source.")
        rows = list(csv.DictReader(StringIO(decision_csv_with_provenance([decision], first, second, "c" * 64).decode("utf-8-sig"))))
        self.assertEqual(rows[0]["comparison_id"], "c" * 64)
        self.assertEqual(rows[0]["first_source_sha256"], "a" * 64)
        self.assertEqual(rows[0]["second_source_sha256"], "b" * 64)
        self.assertEqual(rows[0]["first_worksheet"], "Sheet A")
        self.assertEqual(rows[0]["second_worksheet"], "")
        self.assertEqual(json.loads(rows[0]["first_column_mapping"]), mapping)
        self.assertEqual(rows[0]["first_source_filename"], "'=formula-name.csv")
        self.assertEqual(first.name, "=formula-name.csv")


if __name__ == "__main__":
    unittest.main()
