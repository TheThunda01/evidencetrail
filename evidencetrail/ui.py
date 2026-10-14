"""Small interface helpers for loading sources and keeping session state local."""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from .audit import REQUIRED_COLUMNS
from .decisions import DECISION_COLUMNS
from .io import list_sheets, load_table
from .mapping import map_columns, suggest_mapping
from .reports import spreadsheet_safe_frame


ROOT = Path(__file__).resolve().parents[1]
FIELD_LABELS = {
    "record_id": "Record ID", "report_id": "Report ID", "field": "Extraction field",
    "value": "Extracted value", "evidence_status": "Evidence status",
    "source_locator": "Source location", "review_status": "Review status",
}


@dataclass
class Source:
    """One mapped source plus the information needed to identify its input."""

    frame: pd.DataFrame
    name: str
    digest: str
    sheet: str | None
    mapping: dict[str, str]

    def metadata(self) -> dict:
        return {
            "filename": self.name, "sha256": self.digest, "worksheet": self.sheet,
            "column_mapping": dict(self.mapping),
        }


def clear_session() -> None:
    """Discard this session's widget state and unsaved decision log."""
    generation = st.session_state.get("_upload_generation", 0) + 1
    st.session_state.clear()
    # Changing uploader identity also removes the browser's selected-file state.
    st.session_state["_upload_generation"] = generation


def upload_widget_key(prefix: str) -> str:
    return f"{prefix}_upload_{st.session_state.get('_upload_generation', 0)}"


def load_source(prefix: str, example: str | None = None, label: str = "Extraction spreadsheet") -> Source | None:
    """Load an example or upload, then apply a user-visible column mapping.

    Mapping and worksheet widgets are tied to the exact input bytes. A new
    file therefore cannot inherit another file's column choices by accident.
    """
    if example is None:
        upload = st.file_uploader(
            label, type=["csv", "xlsx"], key=upload_widget_key(prefix),
            help="UTF-8 CSV or Excel .xlsx. Up to 5 MiB, 10,000 rows and 50 columns.",
        )
        if upload is None:
            return None
        source_name, source_bytes = upload.name, upload.getvalue()
    else:
        source_name = Path(example).name
        source_bytes = (ROOT / "examples" / source_name).read_bytes()
    digest = sha256(source_bytes).hexdigest()
    sheet = None
    try:
        if source_name.lower().endswith(".xlsx"):
            sheets = list_sheets(source_bytes)
            if not sheets:
                raise ValueError("The workbook has no worksheets to read.")
            sheet = st.selectbox("Worksheet", sheets, key=f"{prefix}_sheet_{digest}")
        raw = load_table(source_name, source_bytes, sheet_name=sheet)
        suggestions = suggest_mapping(raw)
        sheet_key = sha256((sheet or "").encode("utf-8")).hexdigest()[:16]
        mapping = {}
        with st.expander("Match your columns", expanded=any(value is None for value in suggestions.values())):
            st.caption("Choose the column for each required field. These choices change the working view only; your file stays unchanged.")
            options = [None, *raw.columns]
            for canonical in REQUIRED_COLUMNS:
                mapping[canonical] = st.selectbox(
                    FIELD_LABELS[canonical], options,
                    index=options.index(suggestions[canonical]),
                    format_func=lambda value: "Choose a column" if value is None else str(value),
                    key=f"{prefix}_map_{digest}_{sheet_key}_{canonical}",
                )
        if any(value is None for value in mapping.values()):
            st.info("Choose a column for each required field before continuing.")
            return None
        mapped = map_columns(raw, mapping)
    except ValueError as exc:
        st.error(str(exc))
        st.caption("This source could not be prepared. Check the file, worksheet, or column choices and try again.")
        return None
    return Source(mapped, source_name, digest, sheet, mapping)


def decision_csv_with_provenance(decisions: list[dict], first: Source, second: Source, identity: str) -> bytes:
    """Export the current log with source fingerprints and mapping choices."""
    frame = pd.DataFrame(decisions, columns=DECISION_COLUMNS)
    provenance = {"comparison_id": identity}
    for label, source in (("first", first), ("second", second)):
        provenance.update({
            f"{label}_source_filename": source.name,
            f"{label}_source_sha256": source.digest,
            f"{label}_worksheet": source.sheet or "",
            f"{label}_column_mapping": json.dumps(source.mapping, ensure_ascii=False, sort_keys=True),
        })
    for column, value in provenance.items():
        frame[column] = value
    return spreadsheet_safe_frame(frame).to_csv(index=False, lineterminator="\r\n").encode("utf-8-sig")
