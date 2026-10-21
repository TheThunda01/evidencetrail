# Glossary

These definitions describe how terms are used in EvidenceTrail. A status chosen by a reviewer is a recorded statement, not a conclusion independently established by the app.

## Evidence and review terms

| Term | Meaning here |
| --- | --- |
| Evidence synthesis | Bringing together findings from multiple sources to answer a question. A systematic review uses explicit, planned methods for doing this. |
| Study | An investigation, such as a clinical trial. One study may produce several reports. |
| Report | A source document about a study, such as an article, registry entry, or supplement. `report_id` identifies a document, not necessarily a unique study. |
| Record | One row in an extraction table. In this project it represents one field extracted from one report. Bibliographic software may use “record” differently. |
| Extraction field | A defined item to collect, such as the study design or measurement time. |
| Data dictionary | Definitions of fields, allowed values, units, and coding rules. See the [project dictionary](data-dictionary.md). |
| Outcome | A measured characteristic used to describe what happened to participants or a system. An outcome is distinct from a particular numerical result. |
| Effect estimate | A number describing a comparison or relationship, such as a risk ratio. EvidenceTrail does not compute effect estimates. |
| Risk of bias | Concern that study design, conduct, analysis, or reporting systematically distorts a result. It is not the same as random uncertainty or missing table cells. |
| Certainty of evidence | Confidence in a body of evidence for an outcome. GRADE means Grading of Recommendations Assessment, Development and Evaluation; it considers risk of bias, inconsistency, indirectness, imprecision, and publication bias. The app does not perform GRADE assessments. |
| Inconsistency / indirectness / imprecision | Differences among results / a mismatch between evidence and the question / insufficiently precise estimates. These are distinct concerns in evidence appraisal. |
| Publication bias | Distortion because availability of results depends on their nature or direction. |
| Missingness | Information that is absent or unavailable. `Not reported`, `Unclear`, `Not applicable`, and `Explicitly absent` have different meanings; a blank cell cannot distinguish them. |
| Source locator | Text identifying where information appears, such as a page, table, or figure. The app checks its presence, not whether it is accurate. |
| Adjudication / consensus | A person or team resolving a difference between recorded answers. The app stores a decision; it does not make it. |
| Verified | An allowed reviewer-entered status. It does not mean EvidenceTrail opened or verified the source. |
| Pilot | A small trial of a form or workflow before wider use, intended to reveal unclear fields or procedures. |
| Synthetic fixture | Invented data with known intended behavior, used to check software. It is not experimental evidence. |
| DOI / PMID | Digital Object Identifier / PubMed identifier. They help locate a publication; they are not evidence that its claims are correct. |
| AI / LLM | Artificial intelligence / large language model, a model trained to generate or process language. Findings from a specific model and task do not automatically apply to other versions or uses. |

## Comparison and computing terms

| Term | Meaning here |
| --- | --- |
| Exact-text agreement | Entries match after the documented trimming of surrounding whitespace. Equivalent meanings may still have different text; matching text may share an error. |
| Nonblank agreement | Exact agreement among pairs where both entries in the compared column are nonblank. It has a different denominator from overall agreement. |
| Pairing coverage | Number of paired rows divided by all submitted rows for that reviewer, including rows blocked from comparison. |
| Numerator / denominator | The counted part / the reference total in a fraction. A rate with a zero denominator is undefined, not zero. |
| Cohen's kappa | A chance-corrected agreement statistic for a specified rating scheme. This project does not calculate it. |
| Confidence interval | A statistical procedure's interval for estimating a parameter under specified assumptions. Counts in this app are descriptive and do not include such intervals. |
| Key / composite key | A value used to identify a record; a composite key combines fields. Reviewer pairing uses `(report_id, field)` and requires unique, nonblank keys. |
| Schema | The expected structure and allowed contents of a file or record. Schema validity is not scientific validity. |
| Provenance | Information about origin and processing. A recorded filename or reviewer name does not independently prove origin or identity. |
| SHA-256 / digest / fingerprint | Secure Hash Algorithm with a 256-bit output; a digest is its fixed-size fingerprint of exact bytes. It is not encryption or a signature. |
| Manifest / payload | A list describing exported files / the files being described. The manifest lists sizes and hashes for five payload files. |
| Integrity / authenticity | Whether bytes match a reference / whether origin or identity is established. An unsigned manifest supports the first, not the second. |
| CSV / XLSX / JSON / ZIP | Comma-separated values table / Excel workbook / JavaScript Object Notation structured text / an archive holding files. Each is a file format, not an assurance of data quality. |
| PDF / UTC / KiB | Portable Document Format / Coordinated Universal Time, used for timestamps / a kibibyte, or 1,024 bytes. |
| CRC | Cyclic redundancy check, an error-detection calculation used by ZIP. It is not a cryptographic signature. |
| UTF-8 / BOM | A character encoding / a byte-order mark that can appear at the start of a text file. Changing encoding can change a file fingerprint. |
| MiB / byte | A mebibyte is 1,048,576 bytes; a byte is a unit of digital storage. File-size limits are resource limits, not scientific sample-size requirements. |
| CLI / API / UI | Command-line interface / application programming interface / user interface. These are ways a person or program interacts with software. |
| Backend / CDN | A server-side service / a content delivery network that serves assets. A local browser workflow can still request its page and scripts from a host. |
| Session / persistent storage | Temporary working state / data saved beyond the working session. Downloads remain on disk after the app is cleared. |
| Escaping / parsing | Making special characters display safely / interpreting file structure. Neither interprets the scientific meaning of an answer. |
| XML / DTD / entity | Extensible Markup Language / document type definition / a replaceable reference in XML. Workbook input restricts these features to reduce unsafe parsing behavior. |
| RFC | Request for Comments, a technical-document series. RFC 8493 describes BagIt; this project does not claim to implement that format. |
| Parity test | A check that Python and browser implementations produce matching specified outputs for the same fixtures. It does not establish effectiveness with real reviewers. |

See [concepts](biology-and-concepts.md), [assumptions](assumptions.md), and [references](references.md) for context and source support.
