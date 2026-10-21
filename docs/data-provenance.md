# Data provenance

Terminology: [glossary](glossary.md). For assumptions and their limits, see [assumptions](assumptions.md).

All bundled extraction tables are synthetic software fixtures. `scripts/build_examples.py` defines the fictional records, five planted issues, and paired-reviewer differences. [Expected findings](../examples/expected_findings.json) document the known audit outcome. They are not observations from real studies.

Uploaded tables remain user-supplied evidence. The app records a SHA-256 fingerprint of uploaded bytes, selected worksheet, and column mapping; it does not establish where the data originated or whether a locator supports the answer. The source upload is not embedded in the audit ZIP. The new artifact manifest fingerprints exported payload files separately from the input-file fingerprint.

Keep source permissions and the original research context with your own records. Audit exports can contain identifiers and field names; comparison and decision exports also contain answers. A matching hash does not make those data anonymous, accurate, or suitable for redistribution.
