# The evidence-science concepts behind EvidenceTrail

EvidenceTrail works with records about research, rather than biological measurements themselves. Understanding the difference helps explain both its usefulness and its limits. The examples below are invented teaching examples, not findings from a study.

## A study, a report, and an outcome are different things

A **study** is an investigation. A **report** is a document describing it: a journal article, registry entry, conference abstract, or follow-up paper. One study can produce several reports. An **outcome** is something measured, such as a questionnaire score at a specified time. A study can measure several outcomes, and one outcome can have several analyses or time points.

Cochrane recommends identifying and linking reports from the same study [1]. Counting three papers from one trial as three independent trials would misrepresent the evidence. EvidenceTrail's `report_id` identifies a source document; it does not establish that the document represents a unique study. Likewise, its extraction-row count is not a count of participants, studies, or independent results.

For comparison, each `(report_id, field)` pair must identify one answer. Distinct time points or analyses need sufficiently specific field labels or a separately designed table. The software does not infer these relationships.

## Missing information is not the same as absence

Imagine a report that says nothing about participant withdrawals. A blank extraction cell does not tell us whether there were no withdrawals, the report omitted them, or the reviewer has not checked. A data dictionary should make these possibilities explicit.

EvidenceTrail distinguishes `Not reported`, `Unclear`, `Explicitly absent`, and `Not applicable`. These are recorded interpretations supplied by the reviewer, not facts established by software. `Explicitly absent` means the cited source supports an absence statement; it does not prove that an event never occurred. `Not applicable` means the question does not apply under the team's rules, not that its answer is zero.

The app checks for a value when a row is `Reported`, and for a locator when it is `Reported` or `Explicitly absent`. It does not demand an invented answer for optional fields. Literal text such as `NA` remains text, so a placeholder can satisfy a presence check without supplying useful evidence.

## An effect estimate is not a certainty rating

An **effect estimate** describes the size and direction of a comparison under a specified analysis. Its interpretation depends on the outcome, scale, groups, time point, and study design. A confidence interval represents statistical uncertainty under the analysis assumptions; it does not account automatically for every source of bias.

**Certainty of evidence** is a broader judgment. For intervention questions, GRADE considers a body of evidence for a particular outcome, including risk of bias, inconsistency, indirectness, imprecision, and publication bias [2]. A precise estimate may still have important limitations. Certainty is not a property that can be assigned from the number of populated spreadsheet cells.

EvidenceTrail neither calculates effects nor performs meta-analysis, risk-of-bias assessment, or GRADE. It can help keep the supporting records inspectable before those separate tasks.

## Exact agreement is not correctness or reliability

Two reviewers can copy the same incorrect number. They can also record equivalent answers using different wording. EvidenceTrail compares trimmed text, preserving case and internal spacing; it does not judge semantic equivalence.

Its nonblank agreement denominator includes only matched pairs with text on both sides, separately for each compared column. Blank pairs are counted separately. Pairing coverage uses all submitted rows, including blocked rows, so excluded records do not disappear from that denominator.

These are descriptive summaries of the supplied tables, not estimates of reviewer accuracy or a validated reliability scale. A trial of double extraction found that errors remained after cross-checking in its particular binary-outcome tasks [3]; it does not supply a universal error rate for reviews or validate this app. The practical lesson is to return to the source when resolving a disagreement—and to remember that agreement can share an error.

## Why preserve the decision trail?

A useful decision record retains both answers, the chosen resolution, who recorded it, and the reason. Methods work by Afifi and colleagues emphasizes explicit data structure, comparison, and adjudication [4]. EvidenceTrail follows that general design principle while using its own implementation.

A file fingerprint identifies input bytes; it does not authenticate a publication or verify an extraction. Session decisions can be replaced, and downloaded files can be edited. This is not an append-only or tamper-proof research record. Preserve exports in the team's agreed records system.

The field-completeness download makes another denominator visible: **provided locators / rows requiring locators**. A field containing only `Not applicable` rows has an undefined locator-coverage rate, not zero or 100%. Even 100% means only that required locator text was present.

## Related tools and ideas

- [ASReview](https://github.com/asreview/asreview) learns from screening labels to prioritize records. Its explicit separation of human labels and model output is useful context; EvidenceTrail does not train a screening model.
- [revtools](https://github.com/mjwestgate/revtools) supports bibliographic import, duplicate inspection, and screening in R. Bibliographic duplicates differ from duplicate extraction-row identifiers.
- [Cochrane RevMan](https://revman.cochrane.org/info/features) supports study-data management and meta-analysis. EvidenceTrail is a narrower spreadsheet companion, not an alternative analysis engine.

These comparisons describe documented functions, not tested integrations or relative performance. No code from these tools was copied for this extension.

## Sources

1. Li, Higgins, and Deeks. [Cochrane Handbook, Chapter 5: Collecting data](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05), especially §§5.2.1 and 5.5.
2. Schünemann and colleagues. [Cochrane Handbook, Chapter 14: Summary of findings and certainty](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14).
3. Tang et al. (2025). *Effects of double data extraction on errors in evidence synthesis.* [doi:10.1093/postmj/qgae195](https://doi.org/10.1093/postmj/qgae195).
4. Afifi, Stryhn, and Sanchez (2023). *Data extraction and comparison for complex systematic reviews.* [doi:10.1186/s13643-023-02322-1](https://doi.org/10.1186/s13643-023-02322-1).

Sources and tool documentation checked on October 20, 2026. Guidance and published studies inform the design; they do not demonstrate that EvidenceTrail improves review outcomes.
