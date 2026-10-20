# Practical use

## Where this fits

Use EvidenceTrail between preparing an extraction table and discussing corrections or disagreements with another reviewer. It helps expose the table's structure and preserves a reviewable export. It does not read the underlying reports. The new bundle verifier adds a handoff check: are the exported files still the bytes described by their manifest?

## Input and output contract

The app accepts UTF-8 CSV and, in Python, one selected XLSX sheet. The seven required fields, allowed statuses, file limits, and comparison keys are defined in the [data dictionary](data-dictionary.md) and [methods](methods-and-limitations.md). Mapping changes the working column names, not source values.

A Python audit ZIP now contains five payloads plus `artifact-manifest.json`. The payloads remain `audit-summary.md`, `findings.csv`, `source-manifest.json`, `review-progress.json`, and `field-completeness.csv`. The artifact manifest uses schema `evidencetrail-artifacts/1`, SHA-256, and each payload's path and byte count. It does not hash itself. The input-file fingerprint remains a separate field in the source manifest.

`python -m evidencetrail.verify_bundle FILE.zip` reads at most 64 MiB of compressed data, rejects archives larger than 128 MiB when expanded, limits the manifest to 64 KiB, and never extracts members to disk. It requires exactly the six documented members, unique names, and a valid manifest. Exit `0` means all five payload hashes and lengths match; exit `1` means a readable package has a mismatch; exit `2` means the input or package format could not be verified. The JSON output includes the entire ZIP's fingerprint and individual mismatch codes. Old five-member bundles have no integrity manifest and are explicitly unsupported: regenerate them from the original table.

This is a custom EvidenceTrail package, not a BagIt or RO-Crate implementation. The browser demo has no ZIP exporter; its existing CSV/JSON workflows remain available.

## Worked use case

From the repository root:

```sh
python scripts/bundle_example.py /tmp/evidencetrail-demo.zip
python -m evidencetrail.verify_bundle /tmp/evidencetrail-demo.zip
```

Use a new output path; the example script refuses to overwrite a file. It audits the existing synthetic 20-row fixture and writes a ZIP. A [pinned synthetic bundle](../examples/audit_bundle_v1.zip) and its [verification output](../examples/bundle-verification.json) are also included. The verifier should report `consistent: true` and `checked_payloads: 5`. That outcome means the package is internally consistent, not that its five planted findings were resolved. A reviewer can inspect the findings, return to the fictional or real source as appropriate, and maintain corrections in the team's own records.

## Checks before relying on a result

- Confirm the source filename, source hash, worksheet, and column mapping identify the intended table.
- Inspect finding definitions and denominators, including unmatched reviewer records and missing entries.
- Run the bundle verifier after transferring the ZIP; keep its output with the package if useful.
- Review export contents and source permissions before sharing. Identifiers and field labels can be sensitive even without raw answers.
- Resolve scientific questions against the sources and document who made each decision.

## Known limits

The manifest is unsigned. Someone can change both a payload and its digest, producing a consistent package. Verification does not prove authorship, an unbroken history, source authenticity, extraction accuracy, or research quality. CRC and SHA checks are file-integrity checks only. The app's current decision log is replaceable session state, not an append-only audit trail. A missing locator may warrant attention; a supplied locator is not proof of support.

## Next improvements

1. **Independent manifest preservation:** document a team procedure for storing the ZIP fingerprint separately; acceptance means a transfer test detects replacement against that trusted external digest.
2. **Versioned import:** add an explicit schema migration policy before supporting older bundles; acceptance means unsupported versions fail and migrated fixtures retain record meaning.
3. **Decision history:** explore append-only revisions with source bindings; acceptance means earlier decisions remain recoverable and visible after correction.
4. **User evaluation:** test handoffs using appropriately shareable review exercises; acceptance means prespecified task completion and failure observations are reported separately from extraction accuracy.
