# Contributing to EvidenceTrail

EvidenceTrail is a small research software prototype. Contributions are welcome when they make the checks clearer, the results easier to interpret, or the app easier to run.

## Start with a clear example

For a bug report, describe what you expected, what happened, and how to reproduce it. Include the operating system, Python version, and EvidenceTrail version when relevant.

Use a small synthetic table that reproduces the problem. Do not attach confidential records, participant data, unpublished source material, or access credentials to a public issue or pull request. If an actual research table revealed a problem, recreate the relevant structure with fabricated content.

For a feature suggestion, explain the research task it supports and what a useful result would look like. A concrete example is more helpful than a broad request to add more checks.

## Work locally

Follow the installation instructions in the [README](README.md#run-it-locally). Make your changes on a branch in your fork or local checkout.

Before submitting a change, run:

```sh
python -m unittest discover -s tests -v
```

For an interface change, also run the app and inspect the affected path with synthetic data. Automated audit checks do not establish that the interface is readable or that its controls work as intended.

## Keep the research boundary clear

An audit finding should explain the detected condition and give a useful next step without claiming the science is wrong. Preserve the distinction between missing evidence, unclear evidence, explicitly absent features, and fields that do not apply.

Changes to a rule should include:

- A short explanation of the intended behavior.
- Small examples showing both when the rule should trigger and when it should not.
- Automated checks for meaningful boundary cases.
- Updates to the data dictionary or methods document when the user-facing behavior changes.

Do not introduce external data transfer, persistent storage of uploaded records, or automatic source retrieval without first documenting the need and its data-handling implications. These would change how researchers can use the app.

## Write for researchers

Use direct, familiar language. Name the affected column or row, explain what was found, and describe what the researcher can inspect next. Avoid promising that the tool validates evidence or guarantees a clean dataset.

Keep examples synthetic and internally consistent. Distinguish implemented features from future ideas in documentation and pull requests.

## Submit a focused pull request

Describe the problem, the changed behavior, and how you checked it. Include screenshots when they help explain an interface change. Keep unrelated changes separate so the reasoning is easy to review.
