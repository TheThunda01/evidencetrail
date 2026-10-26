# Practical use

Terminology: [glossary](glossary.md). For assumptions and their limits, see [assumptions](assumptions.md).

## Where this fits

Use EvidenceTrail between preparing an extraction table and discussing corrections or disagreements with another reviewer. It helps expose the table's structure and preserves a reviewable export. It does not read the underlying reports. The new bundle verifier adds a handoff check: are the exported files still the bytes described by their manifest?

## Input and output contract

The app accepts UTF-8 CSV and, in Python, one selected XLSX sheet. The seven required fields, allowed statuses, file limits, and comparison keys are defined in the [data dictionary](data-dictionary.md) and [methods](methods-and-limitations.md). Mapping changes the working column names, not source values.

A Python audit ZIP now contains five payloads plus `artifact-manifest.json`. The payloads remain `audit-summary.md`, `findings.csv`, `source-manifest.json`, `review-progress.json`, and `field-completeness.csv`. The artifact manifest uses schema `evidencetrail-artifacts/1`, SHA-256, and each payload's path and byte count. It does not hash itself. The input-file fingerprint remains a separate field in the source manifest.

`python -m evidencetrail.verify_bundle FILE.zip` reads at most 64 MiB of compressed data, rejects archives larger than 128 MiB when expanded, limits the manifest to 64 KiB, and never extracts members to disk. It requires exactly the six documented members, unique names, and a valid manifest. Exit `0` means all five payload hashes and lengths match; exit `1` means a readable package has a mismatch; exit `2` means the input or package format could not be verified. The JSON output includes the entire ZIP's fingerprint and individual mismatch codes. Old five-member bundles have no integrity manifest and are explicitly unsupported: regenerate them from the original table.

This is a custom EvidenceTrail package, not an implementation of the BagIt packaging standard. The browser demo has no ZIP exporter; its existing CSV/JSON workflows remain available.

**Round 2, 20 October 2026:** `--expected-sha256 HEX` adds a whole-ZIP comparison against a caller-provided reference. Exactly 64 hexadecimal characters are required; uppercase is normalized to lowercase. The new `external_reference` object records the expected digest and whether it matches the received ZIP. `consistent` continues to describe only its five internal payloads. With no option supplied, the old JSON receipt remains unchanged. With the option, exit 0 requires both checks to match, exit 1 reports either mismatch, and exit 2 reports invalid input or a malformed digest. The tool does not discover or authenticate the reference for the caller.

## Worked use case

From the repository root:

```sh
python scripts/bundle_example.py evidencetrail-demo.zip
python -m evidencetrail.verify_bundle evidencetrail-demo.zip
```

Use a new output path; the example script refuses to overwrite a file. It audits the existing synthetic 20-row fixture and writes a ZIP. A [pinned synthetic bundle](../examples/audit_bundle_v1.zip) and its [verification output](../examples/bundle-verification.json) are also included. The verifier should report `consistent: true` and `checked_payloads: 5`. That outcome means the package is internally consistent, not that its five planted findings were resolved. A reviewer can inspect the findings, return to the fictional or real source as appropriate, and maintain corrections in the team's own records.

The [additional example receipt](../examples/bundle-external-verification.json) applies the optional check to the same pinned synthetic ZIP. Its expected digest appears in the README command. This demonstrates format and behavior only: a reference distributed next to a package is not independently trustworthy by virtue of being a different file.

## Checks before relying on a result

- Confirm the source filename, source hash, worksheet, and column mapping identify the intended table.
- Inspect finding definitions and denominators, including unmatched reviewer records and missing entries.
- Run the bundle verifier after transferring the ZIP; keep its output with the package if useful.
- Review export contents and source permissions before sharing. Identifiers and field labels can be sensitive even without raw answers.
- Resolve scientific questions against the sources and document who made each decision.

When using the external-reference option, establish where the expected value came from before running the check. Preserve that record separately from the received ZIP and inspect both `consistent` and `external_reference.matches`. An internally consistent replacement can fail the external comparison.

## Known limits

The manifest is unsigned. Someone can change both a payload and its digest, producing a consistent package. Verification does not prove authorship, an unbroken history, source authenticity, extraction accuracy, or research quality. Cyclic redundancy check (CRC) and Secure Hash Algorithm (SHA) checks are file-integrity checks only. The app's current decision log is replaceable session state, not an append-only audit trail. A missing locator may warrant attention; a supplied locator is not proof of support.

Whole-ZIP fingerprints are sensitive to packaging bytes, including ZIP metadata: a re-created archive can mismatch even when payload content is equivalent. Conversely, a matching digest says nothing about whether a human extraction or recorded judgment was correct. The option does not add digital signatures, identity verification, or an authenticated delivery channel.

## Next improvements

1. **Reference-record workflow:** evaluate how a team stores and retrieves independently trusted ZIP digests; acceptance means operators can detect a deliberately substituted bundle without copying the reference from the received package.
2. **Versioned import:** add an explicit schema migration policy before supporting older bundles; acceptance means unsupported versions fail and migrated fixtures retain record meaning.
3. **Decision history:** explore append-only revisions with source bindings; acceptance means earlier decisions remain recoverable and visible after correction.
4. **User evaluation:** test handoffs using appropriately shareable review exercises; acceptance means prespecified task completion and failure observations are reported separately from extraction accuracy.
