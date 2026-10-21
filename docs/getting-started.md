# Getting started

Terminology: [glossary](glossary.md). For assumptions and their limits, see [assumptions](assumptions.md).

This guide takes you from the synthetic demonstration to auditing a table and comparing reviewer records.

The **browser demo** works with CSV files entirely in your browser and needs no Python or Streamlit account. The **full Python app** also reads Excel workbooks and exports audit ZIP bundles. Follow the [local setup instructions](../README.md#quick-start) for the Python version, or the [hosting guide](deployment.md) to publish the browser demo with GitHub Pages.

The two versions use the same required fields, status meanings, and comparison rules. Their layouts and available downloads differ.

## Browser quick start

1. Open **Audit a table** and choose **Load demo**, then **Run audit**. The example contains 20 rows and five planted findings. **Load clean table** provides a comparison with no findings.
2. To use your own data, select it under **Upload a CSV**, review the seven column assignments, and choose **Run audit**. The file is read in browser memory rather than uploaded to the site host.
3. Inspect the findings and expand **Review evidence status and missing metadata by field**. **Download findings CSV** saves the issues; **Download audit JSON** includes the issues, counts, field summary, source fingerprint, and mapping. The browser does not export Markdown audit reports or ZIP bundles.
4. Open **Compare reviewers**, load the reviewer demo in both panels or select your two CSV files, then choose **Compare reviewers**. Use **Show records** to inspect differences, unmatched records, or locator changes. The comparison JSON includes source information and blocked-key issues alongside the comparison results.
5. Choose a matched **Record to review**, then select a **Decision** and enter the **Reviewer name or identifier** and **Rationale**. Choose **Record decision**. **Download decision CSV** and **Download decision JSON** save the current log. Recording another decision for the same pair replaces its earlier entry.

The browser displays up to 200 rows in each table; downloads contain the full results. Download anything you need before changing comparison sources or mappings, refreshing the page, or choosing **Clear session**. The page does not save sessions in browser storage.

## Full Python app walkthrough

The steps below describe the Python interface. It supports CSV and Excel input and includes the audit ZIP bundle.

## 1. Try the demonstration

To start the full Python app from the project directory:

```sh
python -m streamlit run app.py
```

The Python app opens with **Demo with five issues** selected in the sidebar. You can also choose **Upload a file** and select [demo_records.csv](../examples/demo_records.csv). The Excel equivalent is [demo_records.xlsx](../examples/demo_records.xlsx). The browser demo includes the same synthetic audit example and accepts its CSV version.

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

Copy [extraction_template.csv](../examples/extraction_template.csv), or use an existing table with the same information. The app lets you map your source column names to its seven required fields. Add one row for each extracted field and give every row a unique `record_id`.

For example, three questions answered from one report need three row identifiers but can share one report identifier:

| record_id | report_id | field |
| --- | --- | --- |
| EX-001 | REPORT-001 | Setting |
| EX-002 | REPORT-001 | Data source |
| EX-003 | REPORT-001 | Evaluation method |

Choose `evidence_status` and `review_status` from the exact labels in the [data dictionary](data-dictionary.md). For `Reported`, supply an extracted value and source location. For `Explicitly absent`, supply a source location supporting that interpretation.

CSV files should use commas as separators and UTF-8 encoding; a UTF-8 byte-order mark is accepted. Put the column names in the first row, without a title or introductory paragraph above them. If identifiers contain leading zeros, store them as text in your source table.

The browser demo accepts **CSV only**. To use Excel directly, run the Python app and choose an `.xlsx` file.

The selected Excel sheet must contain values rather than formulas. If it contains formulas, export a separate copy containing values before auditing. The app rejects formulas; it does not calculate them or use cached formula results.

Keep the file within the prototype's limits:

- 5 MiB per file.
- 10,000 data rows, excluding the header.
- 50 columns.

Excel workbooks also have a 25 MiB limit on their expanded contents. An `.xlsx` file is compressed, so this limit differs from its file size on disk.

Literal text such as `NA` or `null` is kept as text. It is not automatically treated as an empty cell. If you mean a cell to be empty, leave it blank; if you mean to describe missing evidence, choose the appropriate evidence status.

## 4. Upload and review

In the Python app, choose **Upload a file**, then select your CSV or Excel file. For a workbook, select the sheet containing the extraction table. In the browser demo, select the CSV from your computer; its contents are read locally in the browser, not sent to the site host. Match each required field to a different source column. Exact matching column names can be selected automatically; other meanings are not guessed.

Mapping does not translate labels such as `Done` into `Verified`, fill missing values, or change your source file. Fix an incorrect label only when you know its intended meaning. Once the mapping is complete, inspect the findings and **Recorded review progress** summary. The **By field** tab shows evidence completeness.

The app reads the selected data and runs the same checks used in the demonstration. It does not fetch documents, open source URLs, or check whether links still work.

The progress summary counts `Pending`, `Verified`, `Disagreement`, and invalid or blank review labels. The completeness table groups rows by their extraction field and shows evidence labels, missing reported answers, and missing required locators. These are descriptions of the uploaded table, not measurements of scientific quality.

Use **Download field completeness CSV** in either version to keep that table. Locator coverage divides provided locators by rows marked `Reported` or `Explicitly absent`; both counts are exported. If no rows require locators, the rate is blank rather than zero. Other status categories remain separate, and locator presence is not source verification.

## 5. Download the audit

Download the outputs you need:

- **`evidencetrail-findings.csv`** lists all findings, including severity, affected row numbers, record IDs, field names, explanations, and suggested next steps.
- **`evidencetrail-audit.md`** records the version, source file, worksheet when relevant, SHA-256 fingerprint, column mapping, counts, and rules checked. It omits individual record IDs, extraction field labels, and extracted answer values; mapped source-column names remain in the report.
- **The audit ZIP bundle, in the Python app only,** combines `audit-summary.md`, `findings.csv`, `field-completeness.csv`, `review-progress.json`, and `source-manifest.json`. It excludes the original upload and raw answers, but includes identifiers, field labels, filenames, and mappings. Review it before sharing.

Downloads always contain the full audit, even when you have filtered the findings on screen. The input file's SHA-256 fingerprint helps distinguish one file version from another. Changing even a single cell usually changes that fingerprint; the fingerprint is not evidence that the extraction is accurate.

To reduce the risk of text being interpreted as a spreadsheet formula, CSV exports and table previews prefix formula-like text with an apostrophe. This applies to text beginning with `=`, `+`, `-`, or `@`, including after leading whitespace. It can affect displayed column names as well as values. Numeric cells keep their numeric values. The audit uses the original values, and your uploaded file remains unchanged.

Keep the audit report with the exact input version it describes. Re-run the audit after making changes. A report from an earlier version does not describe the updated table.

## 6. Compare two reviewers

In the Python app, choose **Compare reviewers** in the sidebar, then **Demo reviewers** to try [reviewer_a.csv](../examples/reviewer_a.csv) with [reviewer_b.csv](../examples/reviewer_b.csv). For your own exports, choose **Upload two files**. Select each workbook's sheet and map each table separately when needed. The browser demo provides the same comparison workflow for two CSV files.

Rows are matched by the combination of **`report_id` and `field`**. Each combination must occur once per table. Record IDs may differ between reviewers. If a key is missing or repeated, the affected rows are blocked; a duplicate on one side also blocks its counterpart on the other. Resolve the structure in your working files and upload them again.

The example produces 19 comparable pairs: 17 agreements and two differences, plus one record present only in each table. Two matched pairs also have different locators. Agreement compares `value` and `evidence_status` after trimming surrounding whitespace. It preserves case and internal spacing. Source-locator differences are shown separately, so an agreement can still need a source-location check.

Open **Pairing coverage and nonblank agreement** to see the denominators. Both example tables have 19 matched rows out of 20 submitted rows, or 95% pairing coverage. The field table separately counts pairs where both cells contain text, only one is blank, or both are blank. Its agreement rate uses only pairs with text on both sides. **Download comparison metrics JSON** saves these counts with the source fingerprints. These are descriptive text comparisons, not accuracy scores.

Reviewers may express the same answer in different words, or share the same incorrect answer. The comparison does not interpret meaning or determine who is correct.

## 7. Record and keep your decisions

For a matched pair, choose **Use first reviewer**, **Use second reviewer**, **Enter a different value**, or **Defer**. Enter your name or reviewer identifier and a reason, including when you defer. A selected or custom `Reported` answer needs a value and locator; an `Explicitly absent` answer needs a locator. These requirements check the record, not its scientific support.

Saving again replaces the current decision for that pair. Current decisions are tied to the two input files, selected worksheets, and column mappings. Changing the comparison clears the current log; switching back does not restore it. Your source files remain unchanged and their review statuses are not automatically updated.

Use **Download decisions CSV** or **Download decisions JSON** before you leave, change comparison inputs, or use **Clear this session**. These exports retain both reviewers' answers and locators as used in the comparison, your current decision and reason, and input provenance. Comparison text has surrounding whitespace trimmed; it is not a copy of the original file's cell formatting. JSON retains that text without spreadsheet escaping; CSV applies spreadsheet escaping. The app has no decision-import or persistent history feature, and a session may be lost when it disconnects or restarts.

## Common questions

### Why is `Not reported` not the same as `Explicitly absent`?

`Not reported` means the reviewed source does not provide the information. `Explicitly absent` means the source supports a statement that the feature is absent. The distinction is a research judgment; the app preserves the labels but cannot determine whether you chose correctly.

### Why are pending rows not flagged?

`Pending` is an allowed review state. It appears in the progress summary but does not itself produce a finding. Your review protocol determines what must be completed before synthesis.

### Why does a row marked `Verified` still have a finding?

The audit rules apply regardless of the review status. A label supplied by a researcher does not override a missing value, duplicate identifier, or another detected problem.

### Can I use confidential records?

Check your research governance requirements and the environment where the app runs. The browser demo processes selected CSV contents locally without transmitting or persisting them; the static host receives ordinary page requests. The Python app processes data on the machine running it, which could be your computer or a separately configured server. Neither version is a research repository or access-control system. Use the synthetic examples for public demonstrations.
