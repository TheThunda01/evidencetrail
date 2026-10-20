"""EvidenceTrail's deterministic extraction-audit and reviewer workspace."""

from hashlib import sha256
import json

import pandas as pd
import streamlit as st

from evidencetrail import __version__
from evidencetrail.audit import EVIDENCE_STATUSES, audit_table
from evidencetrail.comparison import compare_tables, comparison_id
from evidencetrail.decisions import DECISION_CHOICES, decisions_json, make_decision
from evidencetrail.progress import evidence_completeness, review_progress
from evidencetrail.reports import audit_bundle, findings_csv, report_markdown, spreadsheet_safe_frame
from evidencetrail.ui import ROOT, clear_session, decision_csv_with_provenance, load_source, upload_widget_key


ISSUE_NAMES = {
    "MISSING_RECORD_ID": "Missing record ID", "DUPLICATE_RECORD_ID": "Duplicate record ID",
    "MISSING_REPORT_ID": "Missing report ID", "MISSING_FIELD": "Missing field name",
    "INVALID_EVIDENCE_STATUS": "Unrecognized evidence status", "INVALID_REVIEW_STATUS": "Unrecognized review status",
    "MISSING_REPORTED_VALUE": "Missing reported value", "MISSING_SOURCE_LOCATOR": "Missing source location",
    "REVIEWER_DISAGREEMENT": "Reviewer disagreement",
}

st.set_page_config(page_title="EvidenceTrail | Research extraction checks", page_icon="🔎", layout="wide")
st.markdown("""<style>
.stMainBlockContainer { max-width: 1200px; padding-top: 2.8rem; }
h1 { letter-spacing: -0.045em; } h2, h3 { letter-spacing: -0.02em; }
[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
[data-testid="stSidebar"] { border-right: 1px solid #e3e9e7; }
.stDownloadButton button { width: 100%; }
@media (max-width: 640px) { .stMainBlockContainer { padding-top: 1.5rem; } }
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.title("EvidenceTrail")
    st.caption(f"Research extraction checks · v{__version__}")
    workspace = st.radio("Workspace", ["Audit a table", "Compare reviewers"], key="workspace")
    if workspace == "Audit a table":
        mode = st.radio("Choose your data", ["Demo with five issues", "Clean example", "Upload a file"], key="source_mode")
    else:
        mode = st.radio("Choose your data", ["Demo reviewers", "Upload two files"], key="comparison_mode")
    st.divider()
    st.info("Public demo: use only synthetic or non-sensitive data.")
    st.caption("Uploads are sent to the machine hosting this app and processed in session memory. Use a local session for confidential research.")
    st.download_button("Download blank template", (ROOT / "examples/extraction_template.csv").read_bytes(), "extraction_template.csv", "text/csv")
    st.button("Clear this session", on_click=clear_session, key="clear_session", help="Remove this session's uploads, column choices, and current decision log. Download anything you need first.")
    st.caption("Clearing this session does not remove files you already downloaded or control the hosting provider's infrastructure.")
    st.divider()
    st.markdown("**Made for researcher review**")
    st.caption("A person still needs to read the sources and judge the evidence. Recorded statuses and agreement are not independent verification.")

st.title("A clearer trail from finding to source.")


def show_audit() -> None:
    st.write("Check your extraction table, see what needs attention, and take an audit report back to your review.")
    example = {"Demo with five issues": "demo_records.csv", "Clean example": "clean_records.csv"}.get(mode)
    source = load_source("audit", example=example)
    if source is None:
        if mode == "Upload a file" and st.session_state.get(upload_widget_key("audit")) is None:
            st.info("Choose a CSV or Excel file to begin. You can also try the synthetic demo.")
            with st.expander("What should my spreadsheet contain?", expanded=True):
                st.write("Use one row per extracted field and a unique record ID for each row. Several fields can share a report ID. You can match your own column names after uploading.")
                st.code("record_id, report_id, field, value, evidence_status, source_locator, review_status", language=None)
        return
    result = audit_table(source.frame)
    progress = review_progress(source.frame)
    completeness = evidence_completeness(source.frame)
    st.text(source.name + (f" · Worksheet: {source.sheet}" if source.sheet else ""))
    values = [result.records_count, result.report_count, sum(f.severity == "error" for f in result.findings), sum(f.severity == "review" for f in result.findings)]
    for column, label, value in zip(st.columns(4), ["Rows", "Report IDs", "Errors", "Review flags"], values):
        column.metric(label, value)
    st.subheader("Recorded review progress")
    for column, label, key in zip(st.columns(4), ["Pending", "Marked verified", "Disagreements", "Invalid review labels"], ["pending", "verified", "disagreement", "invalid"]):
        column.metric(label, progress[key])
    st.caption("These are statuses supplied in your table. Marked verified does not mean EvidenceTrail checked the source.")
    if result.records_count == 0:
        st.info("This table has the required headers but no extraction rows. Add records before using the audit for your review.")
    elif not result.findings:
        pending = f" {progress['pending']} rows are still marked Pending." if progress["pending"] else ""
        st.info("No issues found by these checks." + pending + " Source support and scientific accuracy still need human review.")
    else:
        st.info(f"{len(result.findings)} findings need attention. The original file has not been changed.")

    findings_tab, field_tab, records_tab, methods_tab = st.tabs(["Findings", "By field", "Records", "How it works"])
    with findings_tab:
        if result.findings:
            left, right = st.columns([1, 2])
            severity = left.selectbox("Show findings", ["All findings", "Data errors", "Review flags"], key="finding_severity")
            query = right.text_input("Search findings", placeholder="Try a record ID, field or rule name", key="finding_search")
            frame = result.to_frame()
            if severity != "All findings":
                frame = frame[frame["severity"] == ("error" if severity == "Data errors" else "review")]
            if query:
                frame = frame[frame.astype(str).apply(lambda row: row.str.contains(query, case=False, regex=False).any(), axis=1)]
            st.caption(f"Showing {len(frame)} of {len(result.findings)} findings. Downloads include the full audit.")
            display = frame[["code", "severity", "row_numbers", "record_id", "field"]].copy()
            display["code"] = display["code"].map(ISSUE_NAMES)
            display["severity"] = display["severity"].map({"error": "Data error", "review": "Review flag"})
            display.columns = ["Issue", "Type", "Rows", "Record", "Field"]
            st.dataframe(spreadsheet_safe_frame(display), hide_index=True, width="stretch")
            st.caption("Row numbers follow the original spreadsheet, with the header on row 1. A duplicate-ID group is one finding listing every affected row.")
            if not frame.empty:
                chosen = st.selectbox("Inspect a finding", list(frame.index), format_func=lambda index: f"{ISSUE_NAMES[frame.loc[index, 'code']]} · row {frame.loc[index, 'row_numbers']}", key="finding_detail")
                st.write(frame.loc[chosen, "message"])
                st.write("**Next step:** " + frame.loc[chosen, "suggestion"])
        else:
            st.write("There are no findings to display.")
        st.subheader("Keep a copy of this audit")
        first, second, third = st.columns(3)
        first.download_button("Download findings CSV", findings_csv(result), "evidencetrail-findings.csv", "text/csv")
        second.download_button("Download audit report", report_markdown(result, source.name, source.digest, sheet_name=source.sheet, column_mapping=source.mapping, review_counts=progress), "evidencetrail-audit.md", "text/markdown")
        third.download_button("Download audit bundle", audit_bundle(result, source.metadata(), progress, completeness), "evidencetrail-audit.zip", "application/zip")
        st.caption("The bundle keeps the findings, field summary, source fingerprint, and column choices together. It does not contain your full input table.")
    with field_tab:
        st.write("See recorded evidence states and missing supporting information for each extraction field.")
        st.dataframe(spreadsheet_safe_frame(completeness), hide_index=True, width="stretch")
        st.caption("Status counts use all rows in each field. Source-locator coverage is provided / required: only Reported and Explicitly absent require a locator here. Not reported, Unclear, Not applicable, and invalid labels remain separate. A blank coverage value means no rows required a locator. A nonblank locator is not verified source support.")
        st.download_button("Download field completeness CSV", spreadsheet_safe_frame(completeness).to_csv(index=False).encode("utf-8-sig"), "evidencetrail-field-completeness.csv", "text/csv")
    with records_tab:
        st.write("Read-only preview with your mapped column names. Literal text such as NA is kept as text.")
        st.dataframe(spreadsheet_safe_frame(source.frame), hide_index=True, width="stretch")
        st.caption("Formula-like text is prefixed with an apostrophe in previews and spreadsheet exports. The audit uses the original values and never rewrites your file.")
        with st.expander("Source fingerprint and column choices"):
            st.code(source.digest, language=None)
            st.json(source.metadata())
            st.caption("The SHA-256 fingerprint identifies exact file bytes. It does not verify their scientific contents.")
    with methods_tab:
        st.subheader("What gets checked")
        st.markdown("""
- Required headers and unique extraction record IDs.
- Missing record IDs, report IDs, and field names.
- Evidence and review statuses against the documented categories.
- Missing values for findings marked **Reported**.
- Missing source locations for **Reported** and **Explicitly absent** findings.
- Records marked **Disagreement** that need a reviewer decision.
""")
        st.write("Data errors indicate an identifier or category that needs correction. Review flags identify missing supporting information or a recorded disagreement. Pending review is counted separately; it does not itself create a finding.")
        st.write("Not reported, Unclear, Explicitly absent, and Not applicable describe different evidence states. The app preserves those categories and never chooses one for you.")
        st.subheader("Data handling and limits")
        st.write("The app does not open source links, read articles, or send records to an AI service. It processes files in the running session without deliberately saving uploads to disk or an application cache. A hosting provider or administrator may still have access to runtime data.")
        st.caption("See the repository's data dictionary and methods notes for the complete input contract, checks, and limitations.")


def show_comparison() -> None:
    st.write("Compare two reviewers' extraction tables, inspect differences, and record decisions with a reason.")
    first_column, second_column = st.columns(2)
    with first_column:
        st.subheader("First reviewer")
        first = load_source("first", "reviewer_a.csv" if mode == "Demo reviewers" else None, "First reviewer's spreadsheet")
    with second_column:
        st.subheader("Second reviewer")
        second = load_source("second", "reviewer_b.csv" if mode == "Demo reviewers" else None, "Second reviewer's spreadsheet")
    if first is None or second is None:
        st.info("Prepare both reviewers' files to compare their records.")
        return
    comparison = compare_tables(first.frame, second.frame)
    identity = comparison_id(first.digest, second.digest, first.sheet, second.sheet, first.mapping, second.mapping)
    if st.session_state.get("active_comparison") != identity:
        st.session_state["active_comparison"] = identity
        st.session_state["decision_log"] = {}
    counts = comparison.summary
    for column, label, value in zip(st.columns(4), ["Comparable pairs", "Exact matches", "Differences", "Unmatched records"], [counts["comparable_pairs"], counts["agreements"], counts["differences"], counts["left_only"] + counts["right_only"]]):
        column.metric(label, value)
    st.caption("Records match on report ID and extraction field. Exact matches compare the value and evidence status, ignoring surrounding whitespace. Source-location differences are shown separately. Agreement does not establish accuracy.")
    if counts["blocked_rows"]:
        st.warning(f"{counts['blocked_rows']} source rows were excluded because a match key was missing or duplicated. A unique counterpart is also excluded when the other reviewer has a duplicate key.")
        with st.expander("Rows that need correction before comparison", expanded=True):
            st.dataframe(spreadsheet_safe_frame(comparison.issues), hide_index=True, width="stretch")
            st.download_button("Download excluded rows CSV", spreadsheet_safe_frame(comparison.issues).to_csv(index=False).encode("utf-8-sig"), "evidencetrail-excluded-rows.csv", "text/csv")
    view = st.selectbox("Show comparison", ["Differences", "All records", "Unmatched records", "Source-location differences"], key="comparison_filter")
    visible = comparison.to_frame()
    if view == "Differences":
        visible = visible[visible["status"] == "Difference"]
    elif view == "Unmatched records":
        visible = visible[visible["status"].isin(["Left only", "Right only"])]
    elif view == "Source-location differences":
        visible = visible[visible["locator_diff"]]
    columns = ["report_id", "field", "status", "left_value", "right_value", "left_evidence_status", "right_evidence_status", "locator_diff"]
    display = visible[columns].copy()
    display.columns = ["Report", "Field", "Comparison", "First value", "Second value", "First evidence status", "Second evidence status", "Source location differs"]
    st.dataframe(spreadsheet_safe_frame(display), hide_index=True, width="stretch")
    st.download_button("Download full comparison CSV", spreadsheet_safe_frame(comparison.to_frame()).to_csv(index=False).encode("utf-8-sig"), "evidencetrail-comparison.csv", "text/csv")
    st.caption("The full comparison includes unmatched records. Excluded rows are provided separately above.")

    with st.expander("Pairing coverage and nonblank agreement", expanded=True):
        st.caption("Coverage uses all submitted rows as its denominator, including rows blocked by missing or duplicated keys. Blank cells are reported separately from agreement on nonblank text.")
        coverage = pd.DataFrame([{
            "Reviewer": "First" if item["reviewer"] == "left" else "Second",
            "Matched / submitted": f"{item['matched_rows']} / {item['input_rows']}",
            "Coverage": "Undefined" if item["coverage_fraction"] is None else f"{item['coverage_fraction']:.1%}",
            "Unmatched rows": item["unmatched_rows"], "Blocked rows": item["blocked_rows"],
        } for item in comparison.metrics["pairing"]])
        st.dataframe(coverage, hide_index=True, width="stretch")
        agreement = pd.DataFrame([{
            "Compared field": item["field"],
            "Exact / both nonblank": f"{item['exact_matches_both_nonblank']} / {item['both_nonblank']}",
            "Nonblank agreement": "Undefined" if item["agreement_fraction_both_nonblank"] is None else f"{item['agreement_fraction_both_nonblank']:.1%}",
            "First blank only": item["left_blank_only"], "Second blank only": item["right_blank_only"],
            "Both blank": item["both_blank"],
        } for item in comparison.metrics["fields"]])
        st.dataframe(agreement, hide_index=True, width="stretch")
        st.caption("Exact matches above can include jointly blank cells. These field rates describe recorded text, not extraction accuracy or reviewer reliability. A blank value may be appropriate for Not reported or Not applicable. There is no meaningful rate when its denominator is zero.")
        metrics_export = {
            "format": "EvidenceTrail comparison metrics", "format_version": 1,
            "application_version": __version__, "comparison_id": identity,
            "first_source": first.metadata(), "second_source": second.metadata(),
            "interpretation": "Descriptive input coverage and nonblank exact-text agreement; not source verification or reviewer reliability.",
            "metrics": comparison.metrics,
        }
        st.download_button("Download comparison metrics JSON", json.dumps(metrics_export, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8"), "evidencetrail-comparison-metrics.json", "application/json")

    st.subheader("Record a review decision")
    eligible = comparison.pairs[comparison.pairs["status"].isin(["Agreement", "Difference"])]
    if eligible.empty:
        st.info("There are no unambiguous matched pairs to review. Correct the match keys or provide overlapping records first.")
        return
    selected = st.selectbox("Matched pair", list(eligible.index), format_func=lambda index: f"{eligible.loc[index, 'report_id']} · {eligible.loc[index, 'field']} ({eligible.loc[index, 'status']})", key=f"pair_{identity}")
    pair = eligible.loc[selected].to_dict()
    pair_key = json.dumps([pair["report_id"], pair["field"]], ensure_ascii=False)
    widget_id = sha256((identity + pair_key).encode("utf-8")).hexdigest()
    left, right = st.columns(2)
    for column, label, side in ((left, "First reviewer", "left"), (right, "Second reviewer", "right")):
        with column:
            st.markdown(f"**{label}**")
            st.text("Value: " + pair[f"{side}_value"])
            st.text("Evidence status: " + pair[f"{side}_evidence_status"])
            st.text("Source location: " + pair[f"{side}_source_locator"])
    saved = st.session_state["decision_log"].get(pair_key)
    if saved:
        st.info("This pair already has a recorded decision. Saving again replaces its entry in the current log; this is not an append-only history.")
    choice = st.selectbox("Decision", DECISION_CHOICES, key=f"choice_{widget_id}")
    with st.form(f"decision_{widget_id}"):
        reviewer = st.text_input("Your name or reviewer ID", value=saved["reviewer"] if saved else "", key=f"reviewer_{widget_id}")
        rationale = st.text_area("Reason for this decision", value=saved["rationale"] if saved else "", key=f"rationale_{widget_id}")
        custom_value = custom_status = custom_locator = ""
        if choice == "Enter a different value":
            custom_value = st.text_area("Chosen value", key=f"value_{widget_id}")
            custom_status = st.selectbox("Chosen evidence status", EVIDENCE_STATUSES, key=f"status_{widget_id}")
            custom_locator = st.text_input("Supporting source location", key=f"locator_{widget_id}")
        submitted = st.form_submit_button("Save decision", key=f"save_{widget_id}")
    if submitted:
        try:
            decision = make_decision(pair, choice, reviewer, rationale, custom_value, custom_status, custom_locator)
            st.session_state["decision_log"][pair_key] = decision
            st.success("Decision recorded for this pair. Neither source table was changed.")
        except ValueError as exc:
            st.error(str(exc))
    decisions = list(st.session_state["decision_log"].values())
    st.caption(f"{len(decisions)} matched pairs have a current decision in this session. A decision does not automatically mark an extraction as verified.")
    if decisions:
        st.dataframe(spreadsheet_safe_frame(pd.DataFrame(decisions)[["report_id", "field", "choice", "status", "reviewer", "rationale"]]), hide_index=True, width="stretch")
    provenance = {"comparison_id": identity, "match_fields": ["report_id", "field"], "compared_fields": ["value", "evidence_status"], "first_source": first.metadata(), "second_source": second.metadata()}
    first_download, second_download = st.columns(2)
    first_download.download_button("Download decisions CSV", decision_csv_with_provenance(decisions, first, second, identity), "evidencetrail-decisions.csv", "text/csv")
    second_download.download_button("Download decisions JSON", decisions_json(decisions, provenance), "evidencetrail-decisions.json", "application/json")
    st.caption("Download the current log before changing source files or clearing the session. Exports retain both original records and source fingerprints; they may contain research data. JSON preserves original text, while spreadsheet exports escape formula-like text.")


if workspace == "Audit a table":
    show_audit()
else:
    show_comparison()
