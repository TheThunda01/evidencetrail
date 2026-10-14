# Changelog

This file records user-facing changes. Version 0.1.0 is the initial working prototype.

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
