# EvidenceTrail: background and purpose

Terminology: [glossary](glossary.md). For assumptions and their limits, see [assumptions](assumptions.md).

## Where this fits

[Review Compass](https://github.com/TheThunda01/review-compass) addresses the earlier task of making a review question and search plan explicit. EvidenceTrail addresses checks on extraction records. They are complementary demonstrations in the portfolio; no automatic transfer between them or validated combined review workflow is implemented. Return to the [portfolio guide](https://github.com/TheThunda01/TheThunda01/blob/main/PROJECT_GUIDE.md).

## The question behind the project

After a review team collects answers from research reports, what should it check before combining the evidence?

An extraction spreadsheet can look complete yet contain missing source locations, inconsistent labels, duplicate records, or unresolved reviewer differences. EvidenceTrail flags these issues and connects review decisions to the submitted records. Researchers still need to check the underlying sources.

## Why build it?

The [Li et al. (2024): Cochrane Handbook's chapter on collecting data](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05) discusses piloting extraction forms, independent extraction, and planning how disagreements will be resolved. [Afifi et al. (2023): Afifi and colleagues' methods paper](https://doi.org/10.1186/s13643-023-02322-1) describes practical steps for defining, comparing, and adjudicating extraction records. These sources motivate the workflow; neither evaluates EvidenceTrail or establishes that it improves review outcomes.

The design starts with a familiar tool: a spreadsheet. Researchers can map their existing column names, inspect findings, and export a record of what needs attention without replacing their whole review process.

## What it does

- Checks extraction-row identifiers, evidence labels, required answers, and source locations.
- Compares two reviewers by report and extraction field, preserving both answers.
- Shows pairing coverage and nonblank text agreement with their denominators and missingness counts.
- Records a reviewer's decision and rationale, then exports findings, decisions, and input fingerprints.

The browser version processes CSV files locally in the browser. The Python app also accepts Excel and provides an audit bundle. Both use temporary working state; the included examples are synthetic.

## Why it matters—and what it cannot tell us

EvidenceTrail aims to help reviewers find a flagged record, understand the problem, check the source, and document their decision.

Matching text can still be wrong, and different wording can mean the same thing. A clean audit, a high agreement rate, or a row marked `Verified` does not establish scientific accuracy. Claims of fewer extraction errors or faster reviews would require a separate evaluation.

**Key themes:** transparent assumptions, explicit denominators, careful handling of missing information, human judgment, and reproducible records.

Start with the [synthetic examples](../README.md#compare-reviewers-and-record-decisions), then read the [methods and limitations](methods-and-limitations.md) before adapting the workflow.
