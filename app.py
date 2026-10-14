"""EvidenceTrail's local, deterministic spreadsheet audit interface."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import streamlit as st

from evidencetrail import __version__
from evidencetrail.audit import audit_table
from evidencetrail.io import list_sheets, load_table
from evidencetrail.reports import findings_csv, report_markdown, spreadsheet_safe_frame


ROOT = Path(__file__).resolve().parent
ISSUE_NAMES = {
    "MISSING_RECORD_ID": "Missing record ID",
    "DUPLICATE_RECORD_ID": "Duplicate record ID",
    "MISSING_REPORT_ID": "Missing report ID",
    "MISSING_FIELD": "Missing field name",
    "INVALID_EVIDENCE_STATUS": "Unrecognized evidence status",
    "INVALID_REVIEW_STATUS": "Unrecognized review status",
    "MISSING_REPORTED_VALUE": "Missing reported value",
    "MISSING_SOURCE_LOCATOR": "Missing source location",
    "REVIEWER_DISAGREEMENT": "Reviewer disagreement",
}

st.set_page_config(page_title="EvidenceTrail | Research extraction checks", page_icon="🔎", layout="wide")
st.markdown(
    """<style>
    .stMainBlockContainer { max-width: 1200px; padding-top: 2.8rem; }
    h1 { letter-spacing: -0.045em; }
    h2, h3 { letter-spacing: -0.02em; }
    [data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
    [data-testid="stSidebar"] { border-right: 1px solid #e3e9e7; }
    .stDownloadButton button { width: 100%; }
    @media (max-width: 640px) { .stMainBlockContainer { padding-top: 1.5rem; } }
    </style>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("EvidenceTrail")
    st.caption(f"Research extraction checks · v{__version__}")
    st.divider()
    selection = st.radio("Choose your data", ["Demo with five issues", "Clean example", "Upload a file"])
    upload = None
    if selection == "Upload a file":
        upload = st.file_uploader("Extraction spreadsheet", type=["csv", "xlsx"], help="UTF-8 CSV or Excel .xlsx. Up to 5 MiB, 10,000 rows and 50 columns.")
        st.caption("Use a local session for unpublished or sensitive research. Uploaded files are processed by the machine running this app.")
    else:
        st.caption("These records are entirely synthetic. They describe no real studies or research findings.")
    st.download_button("Download blank template", (ROOT / "examples/extraction_template.csv").read_bytes(), "extraction_template.csv", "text/csv")
    st.divider()
    st.markdown("**Made for researcher review**")
    st.caption("EvidenceTrail finds gaps and inconsistencies in the table. A researcher still needs to read the source and judge the evidence.")

st.title("A clearer trail from finding to source.")
st.write("Check your extraction table, see what needs attention, and take an audit report back to your review.")

if selection == "Upload a file":
    if upload is None:
        st.info("Choose a CSV or Excel file in the sidebar to begin. You can also try the synthetic demo.")
        with st.expander("What should my spreadsheet contain?", expanded=True):
            st.write("Use one row per extracted field and a unique record_id for each row. Several fields can share a report_id.")
            st.code("record_id, report_id, field, value, evidence_status, source_locator, review_status", language=None)
            st.write("The template includes the required headers. Optional columns can hold reviewer, notes and source_url.")
        st.stop()
    source_name = upload.name
    source_bytes = upload.getvalue()
else:
    source_name = "demo_records.csv" if selection == "Demo with five issues" else "clean_records.csv"
    source_bytes = (ROOT / "examples" / source_name).read_bytes()

sheet = None
try:
    if source_name.lower().endswith(".xlsx"):
        sheets = list_sheets(source_bytes)
        sheet = st.sidebar.selectbox("Worksheet", sheets)
    records = load_table(source_name, source_bytes, sheet_name=sheet)
    result = audit_table(records)
except ValueError as exc:
    st.error(str(exc))
    st.caption("No audit was completed. Correct the file or choose another worksheet and try again.")
    st.stop()

source_hash = sha256(source_bytes).hexdigest()
error_count = sum(f.severity == "error" for f in result.findings)
review_count = sum(f.severity == "review" for f in result.findings)
st.caption(f"{source_name}" + (f" · Worksheet: {sheet}" if sheet else ""))
columns = st.columns(4)
for column, label, value in zip(columns, ["Rows", "Report IDs", "Errors", "Review flags"], [result.records_count, result.report_count, error_count, review_count]):
    column.metric(label, value)

if result.records_count == 0:
    st.info("This table has the required headers but no extraction rows. Add records before using the audit for your review.")
elif not result.findings:
    st.success("No issues found by these checks. Source support and scientific accuracy still need human review.")
else:
    st.info(f"{len(result.findings)} findings need attention. The original file has not been changed.")

findings_tab, records_tab, methods_tab = st.tabs(["Findings", "Records", "How it works"])
with findings_tab:
    if result.findings:
        left, right = st.columns([1, 2])
        severity = left.selectbox("Show findings", ["All findings", "Data errors", "Review flags"])
        query = right.text_input("Search findings", placeholder="Try a record ID, field or rule name")
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
        st.caption("Row numbers refer to the original spreadsheet: the header is row 1. A duplicate-ID group is one finding and lists every affected row.")
        if not frame.empty:
            chosen = st.selectbox(
                "Inspect a finding", list(frame.index),
                format_func=lambda index: f"{ISSUE_NAMES[frame.loc[index, 'code']]} · row {frame.loc[index, 'row_numbers']}",
            )
            selected_finding = frame.loc[chosen]
            st.write(selected_finding["message"])
            st.write("**Next step:** " + selected_finding["suggestion"])
    else:
        st.write("There are no findings to display.")
    st.subheader("Keep a copy of this audit")
    first, second = st.columns(2)
    first.download_button("Download findings CSV", findings_csv(result), "evidencetrail-findings.csv", "text/csv")
    second.download_button("Download audit report", report_markdown(result, source_name=source_name, source_sha256=source_hash, sheet_name=sheet), "evidencetrail-audit.md", "text/markdown")
    st.caption("The report includes the source file fingerprint. Your input spreadsheet is never rewritten.")

with records_tab:
    st.write("Read-only preview of the loaded table. Text such as NA is kept as text; comparison checks ignore surrounding whitespace.")
    st.dataframe(spreadsheet_safe_frame(records), hide_index=True, width="stretch")
    st.caption("For safer spreadsheet downloads, formula-like text in previews is prefixed with an apostrophe. Original values are used for the audit and the input file is unchanged.")
    with st.expander("Source file fingerprint"):
        st.code(source_hash, language=None)
        st.caption("This SHA-256 fingerprint identifies these exact file bytes. It does not verify their scientific contents.")

with methods_tab:
    st.subheader("What gets checked")
    st.markdown("""
    - Required headers and unique extraction record IDs.
    - Missing record IDs, report IDs and field names.
    - Evidence and review statuses against the documented categories.
    - Missing values for findings marked **Reported**.
    - Missing source locations for **Reported** and **Explicitly absent** findings.
    - Records marked **Disagreement** that need a reviewer decision.
    """)
    st.subheader("What the results mean")
    st.write("Data errors indicate an identifier or category that needs correction. Review flags identify a missing value, missing source location, or recorded disagreement. A Pending review alone is not flagged, and a Verified status is not independently confirmed.")
    st.write("Not reported, Unclear, Explicitly absent and Not applicable mean different things. The app preserves those categories and never chooses one for you.")
    st.subheader("Boundaries")
    st.write("The app does not open source links, read articles, check citations against source text, or resolve disagreements. It makes no AI requests. Files stay in the running app's memory and are not deliberately saved by the application; a hosted service's operator can still access its runtime.")
    st.caption("See the repository's data dictionary and methods notes for the complete input contract and limitations.")
