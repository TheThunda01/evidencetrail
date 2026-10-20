# Changelog

This file records user-facing changes. Version 0.1.0 is the initial working prototype.

## Unreleased — advancement round, October 20, 2026

- Round 2 adds an optional independently supplied expected ZIP SHA-256. Default receipts stay unchanged; an external-reference mismatch is reported separately and gives CLI exit 1.

- Added a custom SHA-256 payload manifest to new Python audit ZIPs and an offline verification CLI. Checks establish byte consistency, not scientific verification or source authenticity.
- Added malformed-package, changed-payload, CLI and manifest-boundary tests; existing audit and comparison definitions remain unchanged.
- Standardized README navigation and documented practical use, data provenance, a bounded rapid review, and exact search/screening records.

## 0.3.0 — October 20, 2026

### Added

- Pairing coverage for each reviewer table, using all submitted rows as the denominator, including rows blocked from comparison.
- Separate nonblank exact-text agreement summaries for compared columns, with explicit numerators, denominators, and one-sided or joint blank counts.
- Matching metric definitions in the Python and browser versions, with undefined rates when a denominator is empty.
- Direct field-completeness CSV downloads in both interfaces, including status counts and required/provided source-locator coverage.
- A concepts guide distinguishing studies, reports, outcomes, missing information, effect estimates, evidence certainty, and text agreement.

### Scope

- Overall exact-match counts still include matching blanks. Nonblank agreement answers a separate, narrower question.
- These summaries describe recorded text and comparison coverage. They do not establish extraction accuracy, reviewer reliability, or readiness for synthesis.

## 0.2.0 — October 13, 2026

### Added

- A CSV-only browser demo for GitHub Pages. Its audit, mapping, review summaries, comparison, and current-decision exports run in browser memory without sending selected file contents to a backend. The full Python app retains Excel input and audit ZIP exports.
- Explicit mapping from source-column names to the seven required fields, without changing source values or translating status labels.
- Recorded review-progress counts and evidence-completeness summaries by extraction field.
- A reviewer-comparison workspace that matches records by report ID and field, reports unmatched records, and blocks missing or duplicated match keys.
- Separate displays for differences in answers/evidence status and differences in source locations.
- User-entered decisions with a reviewer name or identifier, rationale, selected answer or deferral, and timestamp. Saving again replaces the current decision for that pair.
- Decision CSV and JSON downloads that preserve both reviewers' submitted values and input provenance; comparison and excluded-row CSV downloads.
- An audit ZIP containing the summary, findings, field completeness, recorded review progress, and source manifest. The original upload and raw answer values are excluded.
- A session-clearing control and synthetic reviewer examples alongside the original 20-row, five-finding audit demonstration.
- An [evidence-informed research review](docs/research-review-2026-10-13.md), updated usage instructions, and documentation of comparison and decision-record limits.

### Hardened

- XLSX input rejects DTD declarations, entity definitions, and external entities using `defusedxml`, in addition to existing file-size, expanded-size, and formula restrictions.

### Scope

- Review statuses and decisions are supplied by researchers; the app does not verify sources or automatically resolve disagreements.
- Current decisions live in session memory and are bound to the inputs, worksheets, and mappings. The app is not a persistent database or an append-only audit history.
- Software checks and synthetic examples do not establish effectiveness in research practice.

## 0.1.0

### Added

- A local Streamlit app for auditing research extraction tables.
- CSV and Excel `.xlsx` input, with sheet selection for workbooks.
- Checks for required and duplicate headers, missing identifiers or field names, duplicate record IDs, invalid status labels, missing reported values, missing required source locations, and reviewer disagreements.
- Downloadable audit output recording the software version, selected Excel worksheet, and input-file SHA-256 fingerprint.
- Formula-like text escaping in CSV exports and table previews, with original values retained for the audit.
- A 20-row synthetic demonstration with five planted findings, a clean CSV example, and a blank extraction template.
- Setup instructions, a data dictionary, and documentation of the audit's methods and limitations.

### Scope

- Files are limited to 5 MiB, 10,000 data rows, and 50 columns.
- Audits check table structure and consistency. Source verification, scientific interpretation, and adjudication remain researcher responsibilities.
