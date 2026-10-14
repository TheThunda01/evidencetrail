# Methods and limitations

EvidenceTrail is a deterministic audit of a structured extraction table. It checks a defined set of file, header, and row conditions. It does not assess the scientific content of an article or perform evidence extraction.

## Unit of checking

One data row represents one extracted field from a report. The row has a unique `record_id`, while `report_id` links related rows to the same report. Repeated report identifiers are expected and are not treated as duplicates.

For Excel workbooks, the audit applies to the selected sheet. It is not an audit of the entire workbook.

## Input boundaries

The supported inputs are comma-separated UTF-8 CSV, including UTF-8 with a byte-order mark, and Excel `.xlsx` workbooks. The prototype accepts a maximum file size of 5 MiB, 10,000 data rows, and 50 columns. The combined expanded contents of an Excel workbook must not exceed 25 MiB.

The selected Excel sheet must contain values rather than formulas. Formula cells cause the input to be rejected; the app does not calculate formulas or substitute cached results. It does not execute workbook macros or follow external workbook links.

Required headers and status labels are documented in the [data dictionary](data-dictionary.md). Surrounding whitespace is ignored for comparisons; case and internal spacing remain significant. Literal strings such as `NA` and `null` remain text, so the application does not silently reinterpret those values as blank cells.

## Checks in version 0.1.0

| Check | Condition that produces a finding or input problem | Interpretation |
| --- | --- | --- |
| Required headers | A required column is missing. | The table does not provide the expected structure. |
| Duplicate headers | A column name occurs more than once. | The app cannot unambiguously associate that name with one column. |
| Required identifiers and field | A row has no `record_id`, `report_id`, or `field`. | The row needs enough context to identify and interpret it. |
| Duplicate record IDs | More than one row uses the same nonblank `record_id`. | Inspect the group and assign or correct identifiers as appropriate. One duplicate group produces one finding. |
| Evidence labels | An `evidence_status` is not one of the five accepted labels. | Choose an allowed label after checking the intended meaning. |
| Review labels | A `review_status` is not one of the three accepted labels. | Correct the label to reflect the actual review state. |
| Reported value | A `Reported` row has a blank `value`. | The status says an answer is available, but the answer is missing. |
| Source location | A `Reported` or `Explicitly absent` row has a blank `source_locator`. | Add the location supporting the extraction or revisit the status. |
| Disagreement | A row has `review_status` set to `Disagreement`. | Researcher review or adjudication remains necessary. |

These checks do not enforce a locator for `Not reported`, `Unclear`, or `Not applicable`. They do not flag `Pending` merely because review is unfinished. A `Verified` row remains subject to all other checks.

One row can produce more than one finding. Conversely, one finding can refer to several rows, as with a duplicated identifier. A finding count is therefore not a count of incorrect extractions, affected articles, or unique research systems.

The app uses `error` for missing required identifiers or fields, duplicate record IDs, and invalid status labels. It uses `review` for missing reported values, missing required source locations, and recorded reviewer disagreements. These are workflow labels, not judgments of scientific validity or importance.

Finding row numbers follow spreadsheet numbering: row 1 is the header, and row 2 is the first data record. Distinct report counts use nonblank `report_id` values. They are not deduplicated study, programme, or system counts.

## What the report can establish

The report records the problems detected by the current rules for the input provided. It includes the EvidenceTrail version and, for an Excel input, the selected worksheet. The SHA-256 fingerprint identifies the input file's bytes, helping distinguish file versions. It does not authenticate an author, establish provenance, or confirm scientific accuracy.

The synthetic demonstration has 20 data rows and five planted findings, described in the [expected-findings file](../examples/expected_findings.json). That known example makes the intended behavior easier to inspect; it is not evidence that the tool detects every possible table problem.

## What the report cannot establish

EvidenceTrail does not:

- Read papers, extract text from PDFs, or compare a table with a source document.
- Judge whether an extracted answer is correct, complete, or appropriate for a research question.
- Decide whether a status such as `Not reported` or `Explicitly absent` is justified.
- Check whether a source location exists or supports the claim.
- Open URLs, verify link availability, or retrieve material from the internet.
- Determine whether two reports describe the same study, programme, configuration, or system.
- Verify that a reviewer actually completed a check or resolve disagreements.
- Assess risk of bias, grade evidence, or establish that a review follows a reporting guideline.

In particular, **zero findings means that no problems were detected by these checks**. It does not mean that the table is ready for publication or that the evidence has been validated.

## Data handling and exports

The app processes uploaded tables in memory. Its application code does not intentionally write uploads to disk, persist extraction tables in an application cache, or send records to an external analysis service. The original input is not edited.

Local use processes records on the machine running the app. In a hosted deployment, that machine is the host's server. Runtime infrastructure, administrators, browser downloads, and the user's own storage practices are outside the audit rules. The prototype does not provide authentication, access controls, or a secure research data repository.

CSV exports and table previews prefix formula-like text with an apostrophe to reduce the risk of spreadsheet formula interpretation. This applies to strings beginning with `=`, `+`, `-`, or `@`, including after leading whitespace. Preview column names receive the same protection; if this makes two names identical, a display suffix distinguishes them. Numeric cells remain numeric. These transformations affect the display or export, not the audit's input values or the uploaded file. Downloaded material can still contain research content and should be handled accordingly.

The findings CSV includes identifiers and field names associated with findings, but does not export the complete input table. The Markdown summary includes the software version, source filename, selected Excel worksheet when applicable, fingerprint, aggregate counts, rule counts, and interpretation guidance. It omits individual record IDs, field names, and extracted values. Source filenames and worksheet names may themselves contain sensitive information, so inspect either output before sharing it.

On-screen filters affect the visible findings only. Both downloaded outputs describe the full audit.

## Reproducibility

Keep the audit output together with the exact input version, the EvidenceTrail version, and any subsequent correction history. Re-run the audit when the table changes. A prior report describes the prior file, even if the filename stays the same.

Automated checks use small, known inputs to exercise the audit rules. They verify software behavior under those conditions; they are not a scientific validation study or a substitute for researcher review.

## Choosing a next action

Treat findings as prompts for inspection. Correct mechanical issues only when the intended value is known. For evidence-dependent issues, return to the source and document the decision using your review's procedures. Preserve uncertainty where the source does not support a confident conclusion.
