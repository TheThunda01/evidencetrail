"""Export audit findings and a reproducible, privacy-conscious summary."""

from collections import Counter
import csv
from io import StringIO, BytesIO
import re
import json
from datetime import datetime, timezone
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd

from . import __version__
from .audit import AuditResult, FINDING_COLUMNS


def _spreadsheet_safe(value: object) -> str:
    """Prefix formula-like text with an apostrophe for spreadsheet CSV readers."""
    text = str(value)
    if text.lstrip(" \t\r\n\v\f\ufeff").startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def spreadsheet_safe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Copy a table with formula-like text escaped for preview CSV downloads.

    Only string values and string column labels are escaped. Numeric values,
    missing values, and their column dtypes are preserved. If escaping causes
    column labels to collide, a display suffix keeps the labels distinct. The
    source table is never modified.
    """
    safe = frame.copy(deep=True)
    for column_position in range(len(safe.columns)):
        for row_position, value in enumerate(safe.iloc[:, column_position]):
            if isinstance(value, str):
                escaped = _spreadsheet_safe(value)
                if escaped != value:
                    safe.iat[row_position, column_position] = escaped
    headers = []
    used: set[object] = set()
    for header in frame.columns:
        base = _spreadsheet_safe(header) if isinstance(header, str) else header
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base} [{suffix}]"
            suffix += 1
        used.add(candidate)
        headers.append(candidate)
    safe.columns = pd.Index(headers, name=frame.columns.name)
    return safe


def findings_csv(result: AuditResult) -> bytes:
    """Return a UTF-8 BOM CSV, with formula-like exported cells escaped."""
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(FINDING_COLUMNS)
    for row in result.to_frame().itertuples(index=False, name=None):
        writer.writerow([_spreadsheet_safe(value) for value in row])
    return output.getvalue().encode("utf-8-sig")


def _markdown_text(text: str) -> str:
    """Escape a single inline label; remove controls that could split the report."""
    text = " ".join(str(text).split())
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_{}\[\]()#+.!|~-])", r"\\\1", text)


def report_markdown(
    result: AuditResult,
    source_name: str,
    source_sha256: str,
    *,
    sheet_name: str | None = None,
    column_mapping: dict[str, str] | None = None,
    review_counts: dict[str, int] | None = None,
) -> str:
    """Summarize counts and rules without including raw extracted values.

    The source SHA-256 identifies uploaded bytes, not scientific validity. The
    summary intentionally omits record IDs, field names, and extracted content;
    individual findings remain available in the separate CSV.
    """
    if not re.fullmatch(r"[0-9a-fA-F]{64}", source_sha256):
        raise ValueError("The source SHA-256 must be a 64-character hexadecimal digest.")
    severity_counts = Counter(finding.severity for finding in result.findings)
    code_counts = Counter(finding.code for finding in result.findings)
    affected_rows = {row for finding in result.findings for row in finding.row_numbers}
    lines = [
        "# EvidenceTrail audit summary",
        "",
        f"EvidenceTrail version: `{__version__}`",
        "",
        f"Source file: {_markdown_text(source_name)}",
        "",
    ]
    if sheet_name is not None:
        lines.extend([f"Selected worksheet: {_markdown_text(sheet_name)}", ""])
    lines.extend([
        f"Source SHA-256: `{source_sha256.lower()}`",
        "",
        f"- Extraction records: {result.records_count:,}",
        f"- Distinct nonempty report IDs: {result.report_count:,}",
        f"- Rules checked: {len(result.checked_rules)}",
        f"- Findings: {len(result.findings):,}",
        f"- Records with findings: {len(affected_rows):,}",
        f"- Errors: {severity_counts['error']:,}",
        f"- Items for review: {severity_counts['review']:,}",
        "",
        "## Findings by rule",
        "",
        "| Rule | Findings |",
        "| --- | ---: |",
    ])
    lines.extend(f"| `{code}` | {code_counts[code]} |" for code in result.checked_rules)
    if review_counts is not None:
        lines.extend(["", "## Review progress as recorded", "", "| Status | Records |", "| --- | ---: |"])
        for key in ("pending", "verified", "disagreement", "invalid"):
            lines.append(f"| {key.capitalize()} | {int(review_counts.get(key, 0))} |")
        lines.extend(["", "These are user-entered statuses. EvidenceTrail has not independently verified the sources."])
    if column_mapping is not None:
        lines.extend(["", "## Column mapping", "", "| Field | Source column |", "| --- | --- |"])
        for field, source_column in column_mapping.items():
            lines.append(f"| {_markdown_text(field)} | {_markdown_text(source_column)} |")
    lines.extend([
        "",
        "A duplicate record-ID group counts as one finding, even when it affects several rows. "
        "Report IDs identify source reports; their count is not a count of distinct studies, programmes, or surveillance systems.",
        "",
        "## Interpretation",
        "",
        "This audit checks table structure and review metadata. It does not read source articles, verify extracted claims, "
        "resolve reviewer disagreements, or establish scientific validity. A clean result means these rules found no issues; "
        "it does not certify the extraction.",
        "",
        "An error identifies a required identifier, extraction field, or controlled status that needs correction. "
        "An item for review identifies missing supporting metadata or a recorded reviewer disagreement. "
        "Pending review alone is not flagged. A Verified status is recorded metadata, not verification performed by EvidenceTrail.",
        "",
        "Not reported, Unclear, Explicitly absent, and Not applicable remain separate statuses. "
        "EvidenceTrail does not infer absence from missing information.",
        "",
        "Spreadsheet row numbers use row 1 for the header and row 2 for the first data record. "
        "Use the findings CSV to locate individual records. This summary omits extracted values and record identifiers.",
        "",
    ])
    return "\n".join(lines)


def audit_bundle(result: AuditResult, source_metadata: dict, review_counts: dict, completeness: pd.DataFrame) -> bytes:
    """Bundle a reproducible audit without embedding the uploaded file.

    Findings include record identifiers and field names. The original extracted
    values are excluded, but the bundle still deserves review before sharing.
    """
    manifest = {
        "application": "EvidenceTrail", "version": __version__,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": source_metadata, "checked_rules": result.checked_rules,
        "original_upload_included": False,
    }
    summary = report_markdown(result, source_metadata["filename"], source_metadata["sha256"],
        sheet_name=source_metadata.get("worksheet"), column_mapping=source_metadata.get("column_mapping"),
        review_counts=review_counts)
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("audit-summary.md", summary)
        archive.writestr("findings.csv", findings_csv(result))
        archive.writestr("source-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.writestr("review-progress.json", json.dumps(review_counts, indent=2))
        archive.writestr("field-completeness.csv", spreadsheet_safe_frame(completeness).to_csv(index=False).encode("utf-8-sig"))
    return output.getvalue()
