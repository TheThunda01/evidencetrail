# Data dictionary

EvidenceTrail uses a table with one row for each extracted field. A report can have many extraction rows. Each row must have a distinct `record_id`, even when it shares a `report_id` with other rows.

## Columns

Column names are lowercase and use underscores. Include all seven required columns, even when some cells are blank. Surrounding whitespace is ignored when checking headers and cell values, but capitalization and internal spaces must match the accepted labels. These comparisons do not rewrite the input table.

| Column | Required header? | Expected content | Example |
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

EvidenceTrail does not assign reviewers, verify the review history, or adjudicate disagreements. These statuses are supplied by the table's authors.

## Blank cells and literal text

Leave a cell blank when it should contain no value. The parser preserves literal text such as `NA`, `N/A`, and `null`; these strings are not automatically converted into missing values. Consequently, a placeholder string can satisfy a nonblank check even when it is not a useful extracted answer. Use the evidence labels deliberately and review placeholder conventions with your team.

Store identifiers as text if their exact form matters. For example, spreadsheet software may otherwise change `0012` into a number before EvidenceTrail receives the file.

Table previews and CSV exports add an apostrophe before formula-like text beginning with `=`, `+`, `-`, or `@`, including after leading whitespace. This display and export precaution can affect text values and displayed column names. It does not change the values used in the audit or the uploaded file.

## Source location examples

A helpful locator is specific enough for another researcher to find the supporting material. Depending on the source, it might be:

- `Methods, p. 4, paragraph 2`
- `Table 2, row “Reporting interval”`
- `Supplementary file 1, section 3.2`
- `Results, subsection “Laboratory reporting”`

The audit only checks whether the required locator cell is nonblank. It does not know whether a page exists or whether the cited passage supports the answer.
