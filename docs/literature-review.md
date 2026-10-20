# Rapid literature and practice review

## Question and scope

What practical changes would make extraction-table review and export easier to inspect without pretending to verify the scientific evidence? This bounded review informed the addition of an integrity manifest and offline checker. It is not a complete systematic review of extraction software or AI effectiveness.

### Round 2 — 20 October 2026

This second scope asks how a recipient can compare an internally consistent bundle with a separately retained expected archive. It happened on the same day as the first review, not after a new period of evidence collection. The implementation is an optional caller-supplied reference comparison, not authentication.

## Search record

On 20 October 2026, PubMed was searched first, with publication dates 2022-01-01 through 2026-10-20 and relevance ordering. The initial query combined systematic review, data extraction, and errors/reproducibility; it returned **293** records. Many first-page titles were clinical reviews merely mentioning extraction, so a title-focused query was used: `"data extraction"[Title] AND (review*[Title] OR meta-analysis[Title])`, returning **55** records. Only the first ten results of each query were screened: **20 distinct titles**, not all 348 hits. Two current methodological publications were selected for detailed appraisal; no pooled effect was calculated. Exact queries, translations, IDs, date fields, page limits, and per-record decisions are in [search-log.json](search-log.json).

The recent papers' abstracts were retrieved through PubMed. Full-text retrieval for Gartlehner et al. failed twice; it remains abstract-only. For Kataoka et al., the first 12,000 of 36,578 body characters were inspected after an initial batch failure; later sections and supplements were not appraised. Targeted official sources supplied data-management guidance and file-manifest semantics. A GitHub BagIt implementation page was unavailable and was not relied on or copied.

The [round-2 search log](search-update-02.json) preserves the new query and decisions. PubMed returned two records for `"data integrity"[Title/Abstract] AND (checksum[Title/Abstract] OR "cryptographic hash"[Title/Abstract]) AND research[Title/Abstract]`, with the same 2022-01-01–2026-10-20 publication window and relevance ordering. Both abstracts concerned SEGUID biological-sequence representations, rather than exact archive bytes, so neither was used to justify this change. They represent preprint/published records of the same underlying work, not two independent studies. Targeted official inspection covered RFC 8493's integrity limits and Python 3.12's SHA-256 API. The original search log is unchanged.

## What the sources support

| Source | Type and access | Relevant finding | Limit | Implementation consequence |
| --- | --- | --- | --- | --- |
| [Gartlehner et al., 2025; PMID 41183336](https://pubmed.ncbi.nlm.nih.gov/41183336/) | Prospective study within six reviews; complete abstract only | The evaluated AI-assisted workflow included human verification; missed items remained an error category. | Particular models, reviews, and adjudication process; no evidence about EvidenceTrail. | Keep source review and decision responsibility explicit; do not label exact agreement as accuracy. |
| [Kataoka et al., 2026; PMID 41626895](https://pubmed.ncbi.nlm.nih.gov/41626895/) | Original development/evaluation study; abstract and opening 12,000 body characters | Performance depended on variable type and dataset; its workflow linked multiple reports and used review-specific extraction instructions. | Small later evaluation datasets, iterative development, incomplete full-text appraisal here. | Preserve source/version context; do not infer evidence support from a text match or import its reported accuracy into this tool. |
| [Cochrane Handbook, chapter 5, v6.5](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05) | Official guidance; chapter inspected; chapter last updated October 2019, handbook 2024 | Data need clear source relationships and durable, shareable records; reports and studies are distinct. | Guidance is not a trial of this software; source linkage still requires judgment. | Retain source manifest, report identifiers, and review decisions as distinct objects. |
| [RFC 8493, October 2018](https://www.rfc-editor.org/rfc/rfc8493) | Official informational file-packaging specification; relevant manifest/integrity sections inspected | File manifests associate paths with cryptographic digests for checking package integrity; they do not secure against deliberate replacement. | EvidenceTrail does not implement the BagIt directory format or claim conformance. | Add a small custom SHA-256 payload manifest, reject ambiguous members, and explicitly distinguish integrity from authenticity. |

The extraction studies motivate cautious, inspectable workflows; they do not establish that adding a checksum reduces extraction mistakes. The manifest change is an engineering response to a local handoff gap: the previous ZIP identified the uploaded source but did not describe the bytes of its exported payload files.

For this technical increment, [RFC 8493 §5.4](https://www.rfc-editor.org/rfc/rfc8493#section-5.4) supports distinguishing manifest consistency from protection against deliberate replacement. [Python 3.12 documentation](https://docs.python.org/3.12/library/hashlib.html) defines hashing bytes and producing a hexadecimal digest. Neither source establishes the trustworthiness of a supplied reference or the correctness of a research result.

| Source | Type/access | Claim used | Limit | Code consequence |
| --- | --- | --- | --- | --- |
| RFC 8493, October 2018, §5.4 | Official specification section inspected | Internal manifests have a limited integrity role. | This package is not BagIt; no signature or source authentication is implemented. | Compare a separately supplied whole-ZIP digest and report it separately. |
| Python 3.12 `hashlib` docs | Official API reference inspected | SHA-256 operates on bytes and returns a hexadecimal digest. | Documentation does not validate the caller's reference. | Validate a 64-hex reference and compare it with the received ZIP bytes. |

## Changes made

`evidencetrail/reports.py` now includes `artifact-manifest.json` in Python audit exports. `evidencetrail/bundle.py` verifies its schema, member names, byte counts, and digests without extracting files. `python -m evidencetrail.verify_bundle` provides a portable check with distinct exit codes. Tests cover changed content, unsupported or ambiguous packages, invalid manifests, and the fact that a jointly replaced manifest and payload can still match. The [worked example](practical-use.md) uses the existing synthetic fixture; no baseline findings or scientific metrics were changed.

No third-party implementation was copied. The checker is original code using Python's standard library; it is not a validation of the RFC or a claim of standards compliance.

Round 2 adds `expected_sha256` to `verify_bundle` and `--expected-sha256` to its CLI. New tests preserve the default receipt, accept a matching reference, reject malformed references, and detect a consistently repackaged replacement against an earlier external digest. A new receipt uses the unchanged pinned synthetic ZIP.

## Remaining work

A team can preserve an external fingerprint or use a separately authenticated repository if authorship and history matter. Durable decision history and schema migration need their own designs and acceptance tests. A practical user study would be needed before claiming that the workflow improves review efficiency or quality.

The comparison completes the earlier optional-reference feature; an actual team still needs a trustworthy reference-storage procedure. Authenticated delivery, signatures, and long-term decision-history storage remain separate requirements, not implemented properties.

## Limits of this review

Searches used one bibliographic database, English query terms, a recent publication window, and only two relevance-ranked pages. Selection was purposive and done by one reviewer with AI assistance. It was not preregistered, independently screened, or exhaustive; publication and indexing delays may omit recent work. Source-specific accuracy or time estimates were deliberately not generalized. The access limitations above are part of the appraisal, not an assumption that unavailable methods were sound.

The round-2 biomedical query produced no directly applicable retained publication. This narrow technical decision rests on official specification/API semantics and executable tests, not a new study of research-workflow effectiveness. The update does not expand the first review into a systematic review.
