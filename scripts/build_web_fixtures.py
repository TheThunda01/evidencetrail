"""Build public browser examples and cross-language fixtures from synthetic data."""

from dataclasses import asdict
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evidencetrail.audit import REQUIRED_COLUMNS, audit_table
from evidencetrail.comparison import compare_tables
from evidencetrail.io import load_table
from evidencetrail.mapping import map_columns
from evidencetrail.progress import evidence_completeness, review_progress


def table(frame):
    return {"headers": list(frame.columns), "rows": frame.to_dict("records")}


def audit_case(name, frame):
    result = audit_table(frame)
    findings = []
    for finding in result.findings:
        row = asdict(finding)
        row.pop("message")
        row.pop("suggestion")
        findings.append(row)
    return {"name": name, "table": table(frame), "expected": {
        "findings": findings, "records_count": result.records_count, "report_count": result.report_count,
        "review_counts": review_progress(frame), "field_summary": evidence_completeness(frame).to_dict("records"),
    }}


def comparison_case(name, left, right):
    result = compare_tables(left, right)
    return {"name": name, "left": table(left), "right": table(right), "expected": {
        "pairs": result.pairs.to_dict("records"), "issues": result.issues.to_dict("records"), "summary": result.summary,
    }}


def main():
    examples = {}
    frames = {}
    for name, filename in [("demo", "demo_records.csv"), ("clean", "clean_records.csv"),
                           ("reviewer_a", "reviewer_a.csv"), ("reviewer_b", "reviewer_b.csv")]:
        content = (ROOT / "examples" / filename).read_bytes()
        examples[name] = {"filename": filename, "csv": content.decode("utf-8-sig")}
        frames[name] = load_table(filename, content)
    (ROOT / "docs/web-examples.json").write_text(json.dumps(examples, ensure_ascii=False, indent=2) + "\n")

    unusual = frames["clean"].iloc[:5].copy()
    unusual.loc[unusual.index[0], "record_id"] = " =1+1 "
    unusual.loc[unusual.index[0], "value"] = " NA "
    unusual.loc[unusual.index[1], "review_status"] = " VERIFIED "
    unusual.loc[unusual.index[2], "evidence_status"] = "Explicitly absent"
    unusual.loc[unusual.index[2], "source_locator"] = ""
    unusual.loc[unusual.index[3], "report_id"] = ""
    unusual.loc[unusual.index[3], "field"] = ""
    unusual.loc[unusual.index[4], "record_id"] = ""
    empty = pd.DataFrame(columns=REQUIRED_COLUMNS)
    aliases = {column: f"Source {index}" for index, column in enumerate(frames["clean"].columns)}
    renamed = frames["clean"].rename(columns=aliases)
    mapping = {column: aliases[column] for column in REQUIRED_COLUMNS}
    duplicate = pd.concat([frames["reviewer_a"], frames["reviewer_a"].iloc[[0]]], ignore_index=True)
    missing = frames["reviewer_b"].copy()
    missing.loc[0, "field"] = ""
    fixtures = {
        "audit_cases": [audit_case("demo", frames["demo"]), audit_case("clean", frames["clean"]),
                        audit_case("unusual values", unusual), audit_case("empty", empty)],
        "mapping_cases": [{"name": "explicit aliases", "table": table(renamed), "mapping": mapping,
                           "expected": table(map_columns(renamed, mapping))}],
        "comparison_cases": [comparison_case("demo reviewers", frames["reviewer_a"], frames["reviewer_b"]),
            comparison_case("duplicate blocks counterpart", duplicate, frames["reviewer_b"]),
            comparison_case("missing key", frames["reviewer_a"], missing), comparison_case("empty", empty, empty)],
    }
    (ROOT / "docs/web-parity.json").write_text(json.dumps(fixtures, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
