"""Check table structure and review metadata without judging scientific claims.

Rows in findings are positional spreadsheet rows: the header is row 1, and the
first data record is row 2. Surrounding whitespace is ignored for comparisons;
the caller's table is never changed.
"""

from collections import defaultdict
from dataclasses import dataclass

import pandas as pd

REQUIRED_COLUMNS = (
    "record_id",
    "report_id",
    "field",
    "value",
    "evidence_status",
    "source_locator",
    "review_status",
)
EVIDENCE_STATUSES = (
    "Reported",
    "Not reported",
    "Unclear",
    "Explicitly absent",
    "Not applicable",
)
REVIEW_STATUSES = ("Pending", "Verified", "Disagreement")
CHECKED_RULES = (
    "MISSING_RECORD_ID",
    "DUPLICATE_RECORD_ID",
    "MISSING_REPORT_ID",
    "MISSING_FIELD",
    "INVALID_EVIDENCE_STATUS",
    "INVALID_REVIEW_STATUS",
    "MISSING_REPORTED_VALUE",
    "MISSING_SOURCE_LOCATOR",
    "REVIEWER_DISAGREEMENT",
)
FINDING_COLUMNS = (
    "code",
    "severity",
    "row_numbers",
    "record_id",
    "field",
    "message",
    "suggestion",
)
MAX_ROWS = 10_000
MAX_COLUMNS = 50


@dataclass(frozen=True)
class Finding:
    """One rule finding, possibly shared by a group of duplicate records."""

    code: str
    severity: str
    row_numbers: tuple[int, ...]
    record_id: str
    field: str
    message: str
    suggestion: str


@dataclass
class AuditResult:
    """The findings and counts produced by the nine documented audit rules."""

    findings: list[Finding]
    records_count: int
    report_count: int
    checked_rules: list[str]

    def to_frame(self) -> pd.DataFrame:
        """Return a display-ready table with stable columns, even if clean."""
        return pd.DataFrame(
            [
                {
                    "code": finding.code,
                    "severity": finding.severity,
                    "row_numbers": ", ".join(map(str, finding.row_numbers)),
                    "record_id": finding.record_id,
                    "field": finding.field,
                    "message": finding.message,
                    "suggestion": finding.suggestion,
                }
                for finding in self.findings
            ],
            columns=FINDING_COLUMNS,
        )


def cell_text(value: object) -> str:
    """Normalize a scalar without interpreting literal NA, null, or nan text."""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def normalize_headers(headers: list[object]) -> list[str]:
    """Trim header labels and reject duplicates before any parser renames them."""
    normalized = [cell_text(header) for header in headers]
    seen: set[str] = set()
    duplicates: list[str] = []
    for header in normalized:
        if header in seen and header not in duplicates:
            duplicates.append(header)
        seen.add(header)
    if duplicates:
        labels = ", ".join(repr(header) for header in duplicates)
        raise ValueError(f"Duplicate column headers: {labels}. Give each column a unique name.")
    return normalized


def audit_table(frame: pd.DataFrame) -> AuditResult:
    """Audit an extraction table; return findings without modifying the input.

    ``error`` means a required identifier, field, or controlled status needs
    correction. ``review`` means metadata calls for a person's attention. Neither
    severity establishes whether an extracted claim is scientifically correct.
    ``report_count`` counts distinct nonempty report IDs, not studies or systems.
    """
    if not isinstance(frame, pd.DataFrame):
        raise ValueError("Provide a pandas DataFrame containing the extraction table.")
    if len(frame) > MAX_ROWS:
        raise ValueError(f"The table has too many records. The limit is {MAX_ROWS:,}.")
    if len(frame.columns) > MAX_COLUMNS:
        raise ValueError(f"The table has too many columns. The limit is {MAX_COLUMNS}.")
    headers = normalize_headers(list(frame.columns))
    missing = [column for column in REQUIRED_COLUMNS if column not in headers]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing) + ".")

    positions = {column: headers.index(column) for column in REQUIRED_COLUMNS}
    findings: list[Finding] = []
    records_by_id: dict[str, list[tuple[int, str]]] = defaultdict(list)
    report_ids: set[str] = set()

    for row_number, row in enumerate(frame.itertuples(index=False, name=None), start=2):
        values = {column: cell_text(row[position]) for column, position in positions.items()}
        record_id, field = values["record_id"], values["field"]
        if values["report_id"]:
            report_ids.add(values["report_id"])
        if record_id:
            records_by_id[record_id].append((row_number, field))

        def add(code: str, severity: str, message: str, suggestion: str) -> None:
            findings.append(Finding(code, severity, (row_number,), record_id, field, message, suggestion))

        if not record_id:
            add("MISSING_RECORD_ID", "error", "The record ID is empty.",
                "Assign a unique ID to this extraction record.")
        if not values["report_id"]:
            add("MISSING_REPORT_ID", "error", "The report ID is empty.",
                "Add the ID of the source report for this record.")
        if not field:
            add("MISSING_FIELD", "error", "The extraction field is empty.",
                "Name the question or field this record addresses.")
        if values["evidence_status"] not in EVIDENCE_STATUSES:
            add("INVALID_EVIDENCE_STATUS", "error", "The evidence status is missing or unrecognized.",
                "Use one of: " + ", ".join(EVIDENCE_STATUSES) + ".")
        if values["review_status"] not in REVIEW_STATUSES:
            add("INVALID_REVIEW_STATUS", "error", "The review status is missing or unrecognized.",
                "Use one of: " + ", ".join(REVIEW_STATUSES) + ".")
        if values["evidence_status"] == "Reported" and not values["value"]:
            add("MISSING_REPORTED_VALUE", "review", "The evidence status is Reported, but the value is empty.",
                "Check the source and add the value, or correct the evidence status.")
        if values["evidence_status"] in ("Reported", "Explicitly absent") and not values["source_locator"]:
            add("MISSING_SOURCE_LOCATOR", "review", "This evidence status needs a source locator, but none is recorded.",
                "Add a page, section, table, figure, or another precise location in the source.")
        if values["review_status"] == "Disagreement":
            add("REVIEWER_DISAGREEMENT", "review", "The record is marked as a reviewer disagreement.",
                "Resolve the disagreement through the project's review process and document the decision.")

    for record_id, occurrences in records_by_id.items():
        if len(occurrences) > 1:
            fields = {field for _, field in occurrences}
            findings.append(Finding(
                "DUPLICATE_RECORD_ID", "error", tuple(row for row, _ in occurrences),
                record_id, occurrences[0][1] if len(fields) == 1 else "",
                "The same record ID is used by more than one row.",
                "Check whether these are duplicate records or distinct extractions that need unique IDs.",
            ))

    rule_order = {code: position for position, code in enumerate(CHECKED_RULES)}
    findings.sort(key=lambda finding: (finding.row_numbers[0], rule_order[finding.code]))
    return AuditResult(findings, len(frame), len(report_ids), list(CHECKED_RULES))
