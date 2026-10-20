"""Describe recorded review states and source-metadata completeness.

These summaries do not verify source support or certify research readiness.
"""

from collections import Counter

import pandas as pd

from .audit import EVIDENCE_STATUSES, REVIEW_STATUSES, cell_text
from .mapping import _headers


COMPLETENESS_COLUMNS = (
    "field", "records", "reported", "not_reported", "unclear", "explicitly_absent",
    "not_applicable", "invalid_evidence_status", "missing_reported_value", "missing_source_locator",
    "source_locator_required", "source_locator_provided", "source_locator_coverage",
)


def _values(frame: pd.DataFrame, columns: tuple[str, ...]):
    headers = _headers(frame)
    missing = [column for column in columns if column not in headers]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing) + ".")
    positions = [headers.index(column) for column in columns]
    return [tuple(cell_text(row[position]) for position in positions)
            for row in frame.itertuples(index=False, name=None)]


def review_progress(frame: pd.DataFrame) -> dict[str, int]:
    """Count recorded review labels without interpreting them as verification.

    Invalid includes blank and unrecognized labels. Counts always sum to records.
    Only ``review_status`` is required; header and table-size checks still apply.
    """
    rows = _values(frame, ("review_status",))
    counts = Counter(status for status, in rows)
    return {
        "records": len(rows),
        "pending": counts["Pending"],
        "verified": counts["Verified"],
        "disagreement": counts["Disagreement"],
        "invalid": sum(count for status, count in counts.items() if status not in REVIEW_STATUSES),
    }


def evidence_completeness(frame: pd.DataFrame) -> pd.DataFrame:
    """Count evidence labels and missing metadata by first-seen extraction field.

    Surrounding whitespace is ignored, but case remains significant and literal
    ``NA`` or ``null`` remains text. Required metadata follows the audit rules:
    Reported needs a value; Reported and Explicitly absent need a source locator.
    Missing-field rows appear under an empty field label rather than disappearing.
    """
    rows = _values(frame, ("field", "evidence_status", "value", "source_locator"))
    groups: dict[str, dict[str, int | str]] = {}
    labels = dict(zip(EVIDENCE_STATUSES, (
        "reported", "not_reported", "unclear", "explicitly_absent", "not_applicable",
    )))
    for field, status, value, locator in rows:
        if field not in groups:
            groups[field] = {column: 0 for column in COMPLETENESS_COLUMNS}
            groups[field]["field"] = field
        group = groups[field]
        group["records"] += 1
        group[labels.get(status, "invalid_evidence_status")] += 1
        group["missing_reported_value"] += int(status == "Reported" and not value)
        group["missing_source_locator"] += int(status in ("Reported", "Explicitly absent") and not locator)
    for group in groups.values():
        required = group["reported"] + group["explicitly_absent"]
        provided = required - group["missing_source_locator"]
        group["source_locator_required"] = required
        group["source_locator_provided"] = provided
        group["source_locator_coverage"] = provided / required if required else None
    result = pd.DataFrame(list(groups.values()), columns=COMPLETENESS_COLUMNS)
    # Keep undefined ratios as None rather than pandas NaN in JSON exports.
    result["source_locator_coverage"] = pd.Series(
        [group["source_locator_coverage"] for group in groups.values()], dtype=object)
    return result
