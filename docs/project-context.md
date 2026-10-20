# EvidenceTrail: background and purpose

## The question behind the project

When a review team has collected answers from research reports, what still needs checking before those answers are used in a synthesis?

An extraction spreadsheet can look complete while hiding missing source locations, inconsistent labels, duplicate records, or unresolved reviewer differences. EvidenceTrail makes those issues visible and keeps the next decision connected to the submitted records. It is a companion to source review, not an automated judge of the evidence.

## Why build it?

The [Cochrane Handbook's chapter on collecting data](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05) discusses piloting extraction forms, independent extraction, and planning how disagreements will be resolved. [Afifi and colleagues' methods paper](https://doi.org/10.1186/s13643-023-02322-1) describes practical steps for defining, comparing, and adjudicating extraction records. These sources motivate the workflow; neither evaluates EvidenceTrail or establishes that it improves review outcomes.

The design starts with a familiar tool: a spreadsheet. Researchers can map their existing column names, inspect findings, and export a record of what needs attention without replacing their whole review process.

## What it does

- Checks extraction-row identifiers, evidence labels, required answers, and source locations.
- Compares two reviewers by report and extraction field, preserving both answers.
- Shows pairing coverage and nonblank text agreement with their denominators and missingness counts.
- Records a reviewer's decision and rationale, then exports findings, decisions, and input fingerprints.

The browser version processes CSV files locally in the browser. The Python app also accepts Excel and provides an audit bundle. Both use temporary working state; the included examples are synthetic.

## Why it matters—and what it cannot tell us

The practical aim is to help a reviewer find a record, understand why it was flagged, return to its source, and document the decision. Matching text can still be wrong, and different wording can mean the same thing. A clean audit, a high agreement rate, or a row marked `Verified` does not establish scientific accuracy. Benefits such as fewer extraction errors or faster reviews would need a separate evaluation.

**Key themes:** transparent assumptions, explicit denominators, careful handling of missing information, human judgment, and reproducible records.

Start with the [synthetic examples](../README.md#compare-reviewers-and-record-decisions), then read the [methods and limitations](methods-and-limitations.md) before adapting the workflow.
