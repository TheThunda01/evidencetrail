"""Create explicit reviewer decisions while preserving both original records."""

from collections.abc import Mapping
from datetime import datetime, timezone
import json

import pandas as pd

from . import __version__
from .audit import EVIDENCE_STATUSES, cell_text
from .reports import spreadsheet_safe_frame

DECISION_CHOICES = ("Use first reviewer", "Use second reviewer", "Enter a different value", "Defer")
DECISION_COLUMNS = (
    "source_key", "report_id", "field", "left_row", "right_row",
    "left_record_id", "right_record_id", "left_value", "right_value",
    "left_evidence_status", "right_evidence_status", "left_source_locator", "right_source_locator",
    "comparison_status", "choice", "value", "evidence_status", "source_locator",
    "status", "reviewer", "rationale", "decided_at",
)


def _timestamp(timestamp: str | None) -> str:
    if timestamp is None:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        value = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("The decision timestamp must be an ISO 8601 date and time with a timezone.") from error
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("The decision timestamp must include a timezone.")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def make_decision(
    pair: Mapping,
    choice: str,
    reviewer: str,
    rationale: str,
    custom_value: str = "",
    custom_evidence_status: str = "",
    custom_source_locator: str = "",
    timestamp: str | None = None,
) -> dict:
    """Record a person's choice; never overwrite sources or claim verification.

    A selected or entered result must meet the same basic evidence-metadata
    requirements. These checks cannot establish whether a source supports it.
    Deferred decisions preserve the originals but contain no selected result.
    """
    if not isinstance(pair, Mapping):
        raise ValueError("Provide one matched comparison record.")
    if cell_text(pair.get("status")) not in ("Agreement", "Difference"):
        raise ValueError("Decisions require a matched pair; unmatched or blocked records need correction first.")
    for side in ("left", "right"):
        if not cell_text(pair.get(f"{side}_row")):
            raise ValueError("Decisions require records from both reviewers.")
        for column in ("record_id", "value", "evidence_status", "source_locator"):
            if f"{side}_{column}" not in pair:
                raise ValueError(f"The comparison record is missing {side}_{column}.")
    if choice not in DECISION_CHOICES:
        raise ValueError("Choose one of: " + ", ".join(DECISION_CHOICES) + ".")
    reviewer, rationale = cell_text(reviewer), cell_text(rationale)
    if not reviewer or not rationale:
        raise ValueError("Record a reviewer name or identifier and a rationale, including for deferred decisions.")
    value = evidence_status = source_locator = ""
    if choice in ("Use first reviewer", "Use second reviewer"):
        side = "left" if choice == "Use first reviewer" else "right"
        value, evidence_status, source_locator = (cell_text(pair[f"{side}_{column}"]) for column in ("value", "evidence_status", "source_locator"))
    elif choice == "Enter a different value":
        value, evidence_status, source_locator = map(cell_text, (custom_value, custom_evidence_status, custom_source_locator))
    if choice != "Defer":
        if evidence_status not in EVIDENCE_STATUSES:
            raise ValueError("The selected result needs a recognized evidence status.")
        if evidence_status == "Reported" and not value:
            raise ValueError("A Reported result needs a value.")
        if evidence_status in ("Reported", "Explicitly absent") and not source_locator:
            raise ValueError("A Reported or Explicitly absent result needs a source locator.")

    metadata = {"status", "different_fields", "locator_diff"}
    key = {str(name): cell_text(item) for name, item in pair.items()
           if name not in metadata and not str(name).startswith(("left_", "right_"))}
    result = {column: cell_text(pair.get(column, "")) for column in DECISION_COLUMNS
              if column.startswith(("left_", "right_")) or column in ("report_id", "field")}
    result.update(
        source_key=json.dumps(key, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        comparison_status=cell_text(pair["status"]), choice=choice,
        value=value, evidence_status=evidence_status, source_locator=source_locator,
        status="Deferred" if choice == "Defer" else "Decision recorded",
        reviewer=reviewer, rationale=rationale, decided_at=_timestamp(timestamp),
    )
    return {column: result[column] for column in DECISION_COLUMNS}


def decisions_csv(decisions: list[dict]) -> bytes:
    """Export a spreadsheet-safe, UTF-8 decision log with stable columns."""
    frame = pd.DataFrame(decisions, columns=DECISION_COLUMNS)
    return spreadsheet_safe_frame(frame).to_csv(index=False, lineterminator="\r\n").encode("utf-8-sig")


def decisions_json(decisions: list[dict], provenance: dict) -> str:
    """Export original text and input provenance without asserting validity."""
    payload = {
        "format": "EvidenceTrail reviewer decisions", "format_version": 1,
        "evidencetrail_version": __version__, "provenance": provenance,
        "interpretation": "These are recorded reviewer decisions, not source verification. Source tables are unchanged.",
        "decisions": decisions,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
