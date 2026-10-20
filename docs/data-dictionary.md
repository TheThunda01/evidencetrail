# Data dictionary

EvidenceTrail uses a table with one row for each extracted field. A report can have many extraction rows. Each row must have a distinct `record_id`, even when it shares a `report_id` with other rows.

The same required fields, evidence labels, and comparison rules apply to both versions. The browser demo reads CSV files in browser memory; the full Python app also reads selected Excel sheets. See [methods and limitations](methods-and-limitations.md) for their different processing and export paths.

## Columns

The names below are EvidenceTrail's internal field names. Include all seven required fields, even when some cells are blank. If your source uses other column names, map each one to its role in the app. Each source column can be mapped once; a mapping that creates duplicate output names is rejected. Unmapped extra columns are retained in the working table.

Mapping changes headers in a copy, not cell values, row order, or your uploaded file. It does not translate synonyms or infer statuses. Surrounding whitespace is ignored when checking headers and cell values, but capitalization and internal spaces remain significant.

| Column | Required field? | Expected content | Example |
| --- | --- | --- | --- |
| `record_id` | Yes | A unique identifier for the extraction row. Must not be blank. | `EX-001` |
| `report_id` | Yes | An identifier linking the row to a report. Must not be blank; may repeat across rows. | `REPORT-001` |
| `field` | Yes | The question or attribute being extracted. Must not be blank. | `Reporting frequency` |
| `value` | Yes | The extracted answer. Required when `evidence_status` is `Reported`. | `Weekly` |
| `evidence_status` | Yes | One of the five evidence labels below. | `Reported` |
| `source_locator` | Yes | A usable location within the source. Required for `Reported` and `Explicitly absent`. | `Methods, p. 4, second paragraph` |
| `review_status` | Yes | One of the three review labels below. | `Pending` |
| `reviewer` | No | The reviewer name or identifier used by your team. | `Reviewer A` |
| `notes` | No | Context, uncertainty, or an explanation supporting later review. | `Check whether timing refers to collection or submission.` |
| `source_url` | No | An optional link to the source. | `https://example.org/synthetic-report` |

All examples in this document are synthetic. A source URL does not replace a source locator: a link identifies a document, while a locator tells the reviewer where to look within it. The app does not open links or verify the accuracy or usefulness of a locator.

## Evidence status

Use these labels exactly, including capitalization and spaces. They describe different evidence states and should not be collapsed into a single missing-data category.

| Label | Intended meaning | Current audit requirement |
| --- | --- | --- |
| `Reported` | The source provides an answer to the field. | Supply a nonblank `value` and `source_locator`. |
| `Not reported` | The reviewed source does not provide the information. | No value or locator requirement is imposed by this prototype. |
| `Unclear` | The source cannot support a confident interpretation. | No value or locator requirement is imposed by this prototype. |
| `Explicitly absent` | The source supports a statement that the feature is absent. | Supply a nonblank `source_locator`. |
| `Not applicable` | The field does not apply to this record under your extraction rules. | No value or locator requirement is imposed by this prototype. |

Your extraction protocol should define when these labels apply. For example, a field that is relevant but unmentioned usually differs from a field that does not apply. EvidenceTrail cannot resolve that distinction for you.

Even where the prototype does not require a locator or note, your protocol may require one. Its absence from the audit rules is not a recommendation to omit documentation.

## Review status

| Label | Intended meaning | Audit behavior |
| --- | --- | --- |
| `Pending` | Review has not been recorded as complete. | Accepted; does not itself create a finding. |
| `Verified` | A researcher has marked the row as checked under the team's process. | Accepted; other checks still apply. |
| `Disagreement` | A reviewer disagreement remains to be resolved. | Creates a finding for researcher review. |

These statuses are supplied by the table's authors. The progress summary counts them as recorded, with blank or unrecognized labels counted as invalid. EvidenceTrail does not establish that the described review took place. A decision recorded in the comparison workflow does not change the source table's `review_status`.

## Field-completeness summaries

The app groups rows by `field` and reports the number of records in each evidence category, invalid evidence labels, missing reported values, and missing required source locations. A row with a blank `field` remains in the summary under a blank label.

These counts describe recorded metadata. A nonblank value such as `NA` can satisfy the presence check while still needing researcher attention. The summary does not judge whether a field is complete enough for your research question.

## Reviewer comparison

The app matches rows using the pair `report_id` and `field`. That pair must be nonblank and unique within each reviewer table. This is stricter than the single-table audit, which permits repeated report/field pairs when each row has a unique `record_id`.

For comparison, represent each distinct question or outcome with an unambiguous field label, or prepare separate comparison tables. Multiple rows for the same report and field cannot be resolved automatically in the current interface. A duplicated key on either side blocks all rows with that key, including a single counterpart on the other side.

| Comparison output | Meaning |
| --- | --- |
| `Agreement` | Both `value` and `evidence_status` match after trimming surrounding whitespace. |
| `Difference` | At least one of those two fields differs. |
| `Left only` / `Right only` | A usable key appears only in the first / second table. |
| `locator_diff` | Matched rows have different `source_locator` text, independently of their agreement status. |
| Blocked row | A missing or ambiguous key prevents safe pairing. |

Record IDs need not match across the two tables. The comparison does not compare reviewer names, notes, or review-status labels to determine agreement. Case and internal spacing still matter; two paraphrases can be reported as a difference.

### Comparison metrics JSON

Both interfaces display these metrics and offer **Download comparison metrics JSON**. The browser's full comparison JSON also includes them under `metrics`. Ratios are proportions from 0 to 1; a zero denominator produces JSON `null`, displayed as **Undefined**.

| Object / field | Definition |
| --- | --- |
| `pairing[].reviewer` | `left` for the first table, `right` for the second. |
| `input_rows` | All submitted rows on that side, including excluded rows. |
| `matched_rows`, `unmatched_rows`, `blocked_rows` | Disjoint counts that sum to `input_rows`. A unique counterpart of a duplicated key is blocked. |
| `coverage_fraction` | `matched_rows / input_rows` on that side. |
| `fields[].field` | Compared column, currently `value` or `evidence_status` in the interfaces. |
| `matched_pairs` | Pairs with unique, complete keys present in both tables. |
| `both_nonblank` | Matched pairs containing nonblank text in this column on both sides. |
| `exact_matches_both_nonblank` | Those nonblank pairs with identical trimmed text. |
| `agreement_fraction_both_nonblank` | `exact_matches_both_nonblank / both_nonblank`. |
| `left_blank_only`, `right_blank_only`, `both_blank` | Remaining matched pairs, classified by blank text in this column. These counts plus `both_nonblank` equal `matched_pairs`. |
| `raw_exact_pair_agreement` | Exact matching across all compared columns, including matching blanks, with `exact_matches`, `matched_pairs`, and their ratio `fraction`. |

Blank values can be appropriate under an evidence-status label. These summaries describe recorded text and pairing coverage; they do not establish correct extraction, reviewer reliability, or scientific validity.

## Decision records

Decisions apply to matched pairs. A name or reviewer identifier and a reason are required for every choice, including deferral.

| Choice | Result |
| --- | --- |
| `Use first reviewer` | Selects the first reviewer's value, evidence status, and source locator. |
| `Use second reviewer` | Selects the second reviewer's corresponding fields. |
| `Enter a different value` | Records a user-entered value, evidence status, and source locator. |
| `Defer` | Records the reason for postponing the decision without selecting an answer. |

A selected result must use an accepted evidence status. `Reported` requires a nonblank value; `Reported` and `Explicitly absent` require a nonblank locator. The recorded decision status is `Decision recorded` or `Deferred`, not `Verified`.

Exports retain source record IDs, row numbers, both reviewers' answers and locators as used in the comparison, comparison status, choice, selected result, reviewer, rationale, and a UTC timestamp. Comparison text has surrounding whitespace trimmed; exact cell formatting is not preserved. Input filenames, file fingerprints, selected sheets, and column mappings identify the comparison. The current session stores one decision per pair; replacing it does not preserve a prior version. Download snapshots if you need to retain a particular state, and use your project's records system for a durable history.

## Blank cells and literal text

Leave a cell blank when it should contain no value. The parser preserves literal text such as `NA`, `N/A`, and `null`; these strings are not automatically converted into missing values. Consequently, a placeholder string can satisfy a nonblank check even when it is not a useful extracted answer. Use the evidence labels deliberately and review placeholder conventions with your team.

Store identifiers as text if their exact form matters. For example, spreadsheet software may otherwise change `0012` into a number before EvidenceTrail receives the file.

CSV exports add an apostrophe before formula-like text beginning with `=`, `+`, `-`, or `@`, including after leading whitespace. Python table previews apply the same precaution, which can affect displayed column names; browser previews render cell contents as text. These precautions do not change the values used in the audit or the original file.

## Source location examples

A helpful locator is specific enough for another researcher to find the supporting material. Depending on the source, it might be:

- `Methods, p. 4, paragraph 2`
- `Table 2, row “Reporting interval”`
- `Supplementary file 1, section 3.2`
- `Results, subsection “Laboratory reporting”`

The audit only checks whether the required locator cell is nonblank. It does not know whether a page exists or whether the cited passage supports the answer.
