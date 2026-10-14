# Getting started

This guide takes you from the synthetic demonstration to an audit of your own extraction table. For installation, follow the commands in the [README](../README.md#run-it-locally).

## 1. Try the demonstration

Start the app from the project directory:

```sh
python -m streamlit run app.py
```

The app opens with **Demo with five issues** selected in the sidebar. You can also choose **Upload a file** and upload [demo_records.csv](../examples/demo_records.csv). The Excel equivalent is [demo_records.xlsx](../examples/demo_records.xlsx).

The demo contains **20 synthetic extraction rows** and **five planted findings**:

| Finding | What to look for |
| --- | --- |
| Duplicate record ID | Two rows share an identifier. The duplicate group produces one finding. |
| Missing source location | A reported answer has no location to check in the source. |
| Invalid evidence status | A status does not match an accepted label. |
| Missing reported value | A row says an answer was reported but leaves the answer blank. |
| Reviewer disagreement | A row is marked `Disagreement`. |

The [expected-findings file](../examples/expected_findings.json) records these deliberately planted issues. The examples are fabricated for learning and testing. They are not findings from a real review.

## 2. Understand the results

The **Findings** tab lists each issue, its type, and the affected rows. Choose **Inspect a finding** to read its explanation and suggested next step. Use the **Records** tab to inspect the input table. Row numbers in findings follow spreadsheet numbering: the header is row 1 and the first data record is row 2. Use the original source when a decision involves the extracted answer or its location.

The type labels help distinguish required table corrections (**Data errors**) from missing supporting information or recorded disagreements (**Review flags**). Downloads call these categories `error` and `review`. They do not grade scientific importance. Filters change which findings you see, not which records the app audits.

The app reports issues; it does not edit the table. Correct your working copy, preserve any change history your review requires, and run the audit again.

Select **Clean example**, or upload [clean_records.csv](../examples/clean_records.csv), to see a table with no findings under the current rules. A clean result is not proof that its scientific content is correct.

## 3. Prepare your own table

Copy [extraction_template.csv](../examples/extraction_template.csv). Keep the column names exactly as written. Add one row for each extracted field and give every row a unique `record_id`.

For example, three questions answered from one report need three row identifiers but can share one report identifier:

| record_id | report_id | field |
| --- | --- | --- |
| EX-001 | REPORT-001 | Setting |
| EX-002 | REPORT-001 | Data source |
| EX-003 | REPORT-001 | Evaluation method |

Choose `evidence_status` and `review_status` from the exact labels in the [data dictionary](data-dictionary.md). For `Reported`, supply an extracted value and source location. For `Explicitly absent`, supply a source location supporting that interpretation.

CSV files should use commas as separators and UTF-8 encoding; a UTF-8 byte-order mark is accepted. Excel files must use the `.xlsx` format. Put the column names in the first row of the selected sheet, without a title or introductory paragraph above them. If identifiers contain leading zeros, store them as text in your source table.

The selected Excel sheet must contain values rather than formulas. If it contains formulas, export a separate copy containing values before auditing. The app rejects formulas; it does not calculate them or use cached formula results.

Keep the file within the prototype's limits:

- 5 MiB per file.
- 10,000 data rows, excluding the header.
- 50 columns.

Excel workbooks also have a 25 MiB limit on their expanded contents. An `.xlsx` file is compressed, so this limit differs from its file size on disk.

Literal text such as `NA` or `null` is kept as text. It is not automatically treated as an empty cell. If you mean a cell to be empty, leave it blank; if you mean to describe missing evidence, choose the appropriate evidence status.

## 4. Upload and review

Choose **Upload a file**, then upload your CSV or Excel file. For a workbook, select the sheet containing the extraction table. The audit runs automatically. Review any file or header problems before interpreting the row-level results.

The app reads the selected data and runs the same checks used in the demonstration. It does not fetch documents, open source URLs, or check whether links still work.

## 5. Download the audit report

Download the two outputs for your records:

- **`evidencetrail-findings.csv`** lists all findings, including severity, affected row numbers, record IDs, field names, explanations, and suggested next steps.
- **`evidencetrail-audit.md`** records the EvidenceTrail version, source file, selected worksheet for Excel inputs, SHA-256 fingerprint, record and report-ID counts, rules checked, and findings by rule. It omits individual record IDs, field names, and extracted values.

Downloads always contain the full audit, even when you have filtered the findings on screen. The input file's SHA-256 fingerprint helps distinguish one file version from another. Changing even a single cell usually changes that fingerprint; the fingerprint is not evidence that the extraction is accurate.

To reduce the risk of text being interpreted as a spreadsheet formula, CSV exports and table previews prefix formula-like text with an apostrophe. This applies to text beginning with `=`, `+`, `-`, or `@`, including after leading whitespace. It can affect displayed column names as well as values. Numeric cells keep their numeric values. The audit uses the original values, and your uploaded file remains unchanged.

Keep the audit report with the exact input version it describes. Re-run the audit after making changes. A report from an earlier version does not describe the updated table.

## Common questions

### Why is `Not reported` not the same as `Explicitly absent`?

`Not reported` means the reviewed source does not provide the information. `Explicitly absent` means the source supports a statement that the feature is absent. The distinction is a research judgment; the app preserves the labels but cannot determine whether you chose correctly.

### Why are pending rows not flagged?

`Pending` is an allowed review state. This prototype highlights explicit disagreements but does not require all rows to be verified. Your review protocol determines what must be completed before synthesis.

### Why does a row marked `Verified` still have a finding?

The audit rules apply regardless of the review status. A label supplied by a researcher does not override a missing value, duplicate identifier, or another detected problem.

### Can I use confidential records?

Check your research governance requirements and the environment where the app runs. Local use processes data on your computer; a hosted instance processes data on its server. The prototype is not a secure repository or access-control system. Use the synthetic examples when demonstrating it publicly.
