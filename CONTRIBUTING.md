# Contributing to EvidenceTrail

EvidenceTrail is a small research software prototype. Contributions are welcome when they make table checks, reviewer comparisons, and decision records clearer or easier to use.

## Start with a clear example

For a bug report, describe what you expected, what happened, and how to reproduce it. Include the operating system, Python version, and EvidenceTrail version when relevant.

Use a small synthetic table that reproduces the problem. Do not attach confidential records, participant data, unpublished source material, or access credentials to a public issue or pull request. If an actual research table revealed a problem, recreate the relevant structure with fabricated content.

For a feature suggestion, explain the research task it supports and what a useful result would look like. A concrete example is more helpful than a broad request to add more checks.

## Work locally

Follow the installation instructions in the [README](README.md#quick-start). Make your changes on a branch in your fork or local checkout.

Before submitting a change, run:

```sh
python -m unittest discover -s tests -v
```

For browser-code changes, also run the parity and boundary checks with Node.js 22 or later:

```sh
node --test tests/web-core.test.mjs
```

Use the [hosting guide](docs/deployment.md#preview-and-checks) to preview the static site. Its CSV-only workflow runs in browser memory; keep file contents out of network requests and persistent browser storage. These parity checks establish behavior on test cases, not effectiveness in research practice.

For an interface change, run the app and inspect the affected path with synthetic data. Useful checks include loading CSV and Excel files, mapping nonstandard column names, handling ambiguous comparison keys, saving and replacing a decision, downloading outputs, and clearing the session. Automated checks do not establish that the interface is readable or that its controls work as intended.

## Keep the research boundary clear

An audit finding should explain the detected condition and give a useful next step without claiming the science is wrong. Preserve the distinction between missing evidence, unclear evidence, explicitly absent features, and fields that do not apply.

Changes to a rule should include:

- A short explanation of the intended behavior.
- Small examples showing both when the rule should trigger and when it should not.
- Automated checks for meaningful boundary cases.
- Updates to the data dictionary or methods document when the user-facing behavior changes.

Keep agreement, a user-recorded decision, and source verification distinct. Preserve both reviewers' source values and the input fingerprints in decision exports. Test missing and duplicate keys rather than silently pairing ambiguous records. Do not describe the current session log as an append-only history: saving again for a pair replaces its current decision.

Do not introduce external data transfer, persistent storage of uploaded records, or automatic source retrieval without first documenting the need and its data-handling implications. These would change how researchers can use the app.

## Write for researchers

Use direct, familiar language. Name the affected column or row, explain what was found, and describe what the researcher can inspect next. Avoid promising that the tool validates evidence or guarantees a clean dataset.

Keep examples synthetic and internally consistent. Distinguish implemented features from future ideas in documentation and pull requests.

For research claims, link the primary source or official guidance and explain its limits. The [research review](docs/research-review-2026-10-13.md) records the rationale behind version 0.2.0. Findings from other software or extraction workflows are not evidence that EvidenceTrail improves accuracy or saves time. Those claims require a suitable evaluation of this app.

## Submit a focused pull request

Describe the problem, the changed behavior, and how you checked it. Include screenshots when they help explain an interface change. Keep unrelated changes separate so the reasoning is easy to review.
