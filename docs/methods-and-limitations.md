# Methods and limitations

EvidenceTrail provides deterministic table checks, recorded-progress summaries, reviewer comparison, and user-entered decision records. It does not assess the scientific content of an article or perform evidence extraction. This document describes version **0.3.0**, which includes a CSV-only browser demo and a full Python app.

## Unit of checking

One data row represents one extracted field from a report. The row has a unique `record_id`, while `report_id` links related rows to the same report. Repeated report identifiers are expected and are not treated as duplicates.

Excel is supported by the Python app only. Its audit applies to the selected sheet, not the entire workbook.

## Input boundaries

Both versions support comma-separated UTF-8 CSV, including UTF-8 with a byte-order mark. Each accepts a maximum file size of 5 MiB, 10,000 data rows, and 50 columns. The Python app also supports Excel `.xlsx` workbooks, whose combined expanded contents must not exceed 25 MiB.

The selected Excel sheet must contain values rather than formulas. Formula cells cause the input to be rejected; the app does not calculate formulas or substitute cached results. It does not execute workbook macros or follow external workbook links.

Workbook XML is checked with `defusedxml` before loading. DTD declarations, entity definitions, and external entities are rejected. These checks limit known input risks; they are not a security certification of an uploaded file or its hosting environment.

Required headers and status labels are documented in the [data dictionary](data-dictionary.md). Surrounding whitespace is ignored for comparisons; case and internal spacing remain significant. Literal strings such as `NA` and `null` remain text, so the application does not silently reinterpret those values as blank cells.

The interface maps seven required fields to explicitly selected source columns. Exact canonical headers can be suggested; synonyms, meanings, and status translations are not inferred. Every required field needs a different source column, and mappings that collide with retained column names are rejected. Mapping operates on a copy without changing values or row order.

## Audit checks

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

Audit outputs record the problems detected by the current rules for the input provided. They identify source files and mapping choices; the Python report also records the application version and selected Excel worksheet when relevant. The SHA-256 fingerprint identifies the input file's bytes, helping distinguish file versions. It does not authenticate an author, establish the origin of research data, or confirm scientific accuracy.

The synthetic demonstration has 20 data rows and five planted findings, described in the [expected-findings file](../examples/expected_findings.json). That known example makes the intended behavior easier to inspect; it is not evidence that the tool detects every possible table problem.

## Progress and completeness

Review progress counts the recorded `Pending`, `Verified`, and `Disagreement` labels. Blank or unrecognized labels are counted as invalid, so the counts sum to the number of records. These are not independently verified completion measures.

Field completeness groups rows by `field`, including blank field labels. It counts each evidence status, unrecognized labels, missing values for `Reported`, and missing locators for `Reported` or `Explicitly absent`. Counts do not measure whether the source was searched adequately, the locator is useful, or the answer is correct. Multiple defects can occur in one row.

Source-locator coverage uses rows marked `Reported` or `Explicitly absent` as its denominator and the subset with nonblank locator text as its numerator. With no required locators the rate is undefined (`null` in JSON, blank in CSV). `Not reported`, `Unclear`, `Not applicable`, and invalid labels remain separate counts rather than being assigned a false zero answer. All submitted extraction rows remain in field counts, including duplicate identifiers. Both interfaces provide a direct CSV download; the Python audit bundle retains the same summary. These are metadata checks, not estimates of search completeness or evidence certainty.

## Reviewer comparison and decisions

The interface matches two tables by `(report_id, field)`. Missing keys are excluded. If a key occurs more than once on either side, all rows with that key on both sides are excluded. The app does not choose among ambiguous matches. Usable keys found only on one side are reported separately.

Matched rows agree only when their `value` and `evidence_status` match after trimming surrounding whitespace. Case and internal spacing remain significant. Different locators are reported independently of answer agreement. Comparison and decision exports contain this trimmed text, rather than the original cell formatting. This is a text comparison, not semantic interpretation, an accuracy estimate, or an agreement statistic adjusted for chance. Review statuses, reviewer names, and notes do not determine the comparison result.

### Comparison metrics

Pairing coverage is calculated separately for each submitted table: the number of matched, unique, complete keys divided by the number of submitted rows on that side. Rows blocked by missing or duplicate keys remain in that denominator, as do usable rows found only on that side. The numerator is the same for both reviewers, but the denominators can differ. A table with no rows has an undefined rate, represented as `null` in JSON. Coverage describes which submitted rows could be compared; it does not measure how completely either reviewer searched a source.

Nonblank agreement is calculated separately for each compared column, currently `value` and `evidence_status`. Among matched keys, the denominator is the number of pairs with nonblank text on both sides, and the numerator is the number of those pairs with identical trimmed text. The summary also counts first-reviewer-only blanks, second-reviewer-only blanks, and joint blanks. These categories make it possible to account for every matched pair without treating a missing entry as an answer. If no pairs contain text on both sides, the rate is undefined rather than zero.

The overall exact-match count retains its original definition: all compared columns must match within a pair, and matching blanks count as text matches. It therefore answers a different question from nonblank agreement. A blank `value` may be appropriate for statuses such as `Not reported` or `Not applicable`; the audit rules and source review determine whether a particular blank needs correction.

These are descriptive counts of the supplied records. Matching text does not establish that an answer is correct or supported, and different text may express the same meaning. The summaries do not establish reviewer reliability, scientific accuracy, or readiness for synthesis. They provide no chance correction or confidence interval. This version does not calculate Cohen's kappa: a pooled statistic over heterogeneous questions and free-text answers would require a separately specified rating scheme and interpretation. The metric definitions here are implementation choices, not a validated measurement scale.

A researcher can select either reviewer's result, enter a different result, or defer. Every decision requires a name or identifier and rationale. Selected results must meet the documented status, value, and locator requirements. These checks do not establish source support.

Decisions are bound to both input-file hashes, mappings, and selected worksheets where relevant. Changing the comparison clears the current decision log; returning to the previous inputs does not restore it. Saving a decision for a pair replaces its previous decision in the current session. It does not create an append-only history or rewrite the input tables. Recorded decisions do not automatically mark source rows as verified. Downloaded files capture the state at the time of export and can subsequently be edited outside the app.

Sessions are temporary. Download needed decisions before leaving or changing comparison inputs. The clear control is **Clear session** in the browser and **Clear this session** in Python. Neither version provides persistent storage, a decision-import workflow, or guaranteed recovery after the page or app closes.

## What the report cannot establish

EvidenceTrail does not:

- Read papers, extract text from PDFs, or compare a table with a source document.
- Judge whether an extracted answer is correct, complete, or appropriate for a research question.
- Decide whether a status such as `Not reported` or `Explicitly absent` is justified.
- Check whether a source location exists or supports the claim.
- Open URLs, verify link availability, or retrieve material from the internet.
- Determine whether two reports describe the same study, programme, configuration, or system.
- Verify that a reviewer actually completed a check or decide how to resolve disagreements.
- Assess risk of bias, grade evidence, or establish that a review follows a reporting guideline.

In particular, **zero findings means that no problems were detected by these checks**. It does not mean that the table is ready for publication or that the evidence has been validated.

## Data handling

The **browser demo** reads selected CSV files and holds working tables and decisions in browser memory. It does not upload their contents, save records in browser storage, or use an analysis backend. Its code and styles are included in the site rather than supplied by a third-party CDN. The static host still receives requests for the page, scripts, and example files. [GitHub documents](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages#data-collection) its ordinary visitor IP logging.

The **Python app** processes uploaded tables and current decisions on the machine running it. Its application code does not intentionally save uploads to disk, retain a persistent research database, or send records to an external analysis service. When it runs locally, that machine is the user's computer; a remotely hosted Python instance receives the uploaded files on its server. Administrators and hosting infrastructure may have access to runtime data.

Neither version edits the original files, provides authentication or a persistent research repository, or controls the user's downloaded copies. Browser extensions, device security, and external storage practices are outside these checks.

## Exports

Both versions prefix formula-like text with an apostrophe in CSV exports to reduce the risk of spreadsheet formula interpretation. This applies to strings beginning with `=`, `+`, `-`, or `@`, including after leading whitespace. The Python app also applies this protection to table previews; the browser renders cells as text. Python preview column names receive the same protection, with suffixes if needed to keep them distinct. Numeric Python cells remain numeric; CSV input cells are text. These transformations do not change the original file or the values used in checks.

The browser demo provides findings CSV, audit JSON, comparison CSV/JSON, and decision CSV/JSON. Audit JSON contains findings, counts, field completeness, source fingerprints, and mapping choices; it excludes the complete source table. Comparison JSON also includes excluded-key issues and input provenance. The browser has no Markdown summary or ZIP export.

The following filenames and bundle details describe the Python app:

| Export | Included information |
| --- | --- |
| Findings CSV | Finding codes, severity, row numbers, record IDs, field labels, explanations, and next steps; not the complete source table. |
| Markdown audit summary | Version, filename, worksheet when relevant, fingerprint, mapping, aggregate counts, rule counts, and interpretation guidance. It omits individual record IDs, extraction field labels, and raw answers, but includes mapped source-column names. |
| Audit ZIP bundle | `audit-summary.md`, `findings.csv`, `field-completeness.csv`, `review-progress.json`, `source-manifest.json`, and `artifact-manifest.json`. The source manifest records inputs, mappings, checked rules, software version, and export time. |
| Reviewer comparison downloads | Compared records and their submitted values, evidence statuses, and locators; blocked-key information is separate. |
| Decision CSV and JSON | Both reviewers' answers and locators as used in comparison, the current decision, reviewer, rationale, timestamp, and input provenance. JSON retains comparison text without CSV escaping; CSV applies spreadsheet escaping. |

The audit bundle excludes the original upload and raw extracted answer values. It still contains record IDs, field labels, filenames, worksheet names, and mappings. Decision and comparison exports include research content. None of these outputs should be treated as anonymized or automatically suitable for public sharing.

On-screen finding filters affect the visible findings only. Audit downloads describe the full audit.

## Reproducibility

Keep audit and decision outputs together with the exact input versions, the EvidenceTrail version, and your project's correction history. Re-run checks when a table changes. A prior report describes the prior file, even if the filename stays the same. The app's current-decision records are not a substitute for a durable history maintained by the research team.

Automated checks use small, known inputs to exercise the audit rules. Browser parity tests compare defined examples against the Python implementation. These checks verify software behavior under those conditions; they are not a scientific validation study or a substitute for researcher review.

The [research review](research-review-2026-10-13.md) documents the evidence and guidance behind these priorities, existing alternatives, and a proposed user pilot. It is not an exhaustive review, and it does not establish that EvidenceTrail reduces extraction errors or workload.

## Choosing a next action

Treat findings as prompts for inspection. Correct mechanical issues only when the intended value is known. For evidence-dependent issues, return to the source and document the decision using your review's procedures. Preserve uncertainty where the source does not support a confident conclusion.


## Export integrity check added after 0.3.0

New Python audit ZIPs add `artifact-manifest.json` with schema `evidencetrail-artifacts/1`. The five payload files each have a byte count and SHA-256; the manifest does not hash itself. `python -m evidencetrail.verify_bundle FILE.zip` checks the declared payload set without extracting files. Legacy ZIPs without this manifest are explicitly unsupported by the checker. The [practical-use contract](practical-use.md) specifies limits, failure behavior, and the distinction between consistency and authenticity. This Python-only packaging change does not alter the existing audit rules, comparison metrics, or browser outputs.

Round 2 adds an optional independently provided whole-ZIP reference comparison. `verify_bundle(content, expected_sha256=...)` preserves the original receipt when no reference is supplied, and adds a separate `external_reference` object otherwise. The CLI returns 1 for an external mismatch even if all internal payloads match their manifest. No audit rule, comparison denominator, source data, or previous example receipt changes.
