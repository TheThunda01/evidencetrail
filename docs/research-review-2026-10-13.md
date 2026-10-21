# Research needs and development decisions

> Editorial note, October 20, 2026: this is a historical development review. Its original search and access descriptions are retained. The [current reference audit](reference-audit.json) records this pass separately. CDC now states that Epi Info product development and technical assistance ended in September 2025; its mention below explains the published workflow and is not a current support recommendation. ASReview's current repository advertises version 3; historical model results below remain version-specific. See [references](references.md#epi-info).

**EvidenceTrail · Evidence-informed product review · October 13, 2026**

EvidenceTrail is intended to help researchers inspect extraction tables, compare reviewer records, and document decisions. The literature supports making these steps easier to follow. It does not establish that EvidenceTrail reduces errors, saves time, or improves the conclusions of a review.

The version 0.2.0 expansion focuses on researchers' existing spreadsheets: clear column mapping, visible review progress, comparisons that retain both reviewers' answers, and an exportable decision record. Automatic extraction from papers is a separate, more demanding problem.

A CSV-only browser version makes these workflows available through static GitHub Pages hosting without a separate application account or a server receiving research files. The Python app retains Excel input and audit ZIP export. This is an implementation choice, not evidence of improved research outcomes; browser parity tests only check specified behavior against known examples.

## Scope and approach

This is a targeted product review, **not a systematic review or a scoping review**. Scientific searches covered **January 1, 2023 through October 13, 2026**. The six selected publications below appeared in 2023–2025. Older material was considered when it remained part of current official guidance.

PubMed searches combined terms for data extraction, systematic reviews, evidence synthesis, errors, reproducibility, large language models, and reviewer needs. One focused search was:

```text
("data extraction"[Title])
AND (error*[Title/Abstract] OR discrepanc*[Title/Abstract]
     OR reproducib*[Title/Abstract])
AND ("2023/01/01"[Date - Publication] : "2026/10/13"[Date - Publication])
```

Additional targeted web searches located original articles and official methods and product documentation. Titles, publication details, identifiers, and abstracts were checked through PubMed. Full texts were read for Afifi et al. and Gartlehner et al.; the other four scientific summaries rely on their indexed abstracts. Cochrane, JBI, Covidence, REDCap, and CDC documents were checked directly on their official sites.

Sources were selected for practical relevance to extraction quality, reviewer comparison, provenance, and usable workflows. There was no registered protocol, exhaustive database search, duplicate screening, or formal risk-of-bias assessment. This selection may miss relevant work, especially outside biomedical evidence synthesis and English-language sources. Vendor documentation establishes described functionality, not independent effectiveness. Links and web documentation were checked on October 13, 2026 and may change.

## What the scientific literature contributes

The final column contains **our development interpretation**, not a feature tested by the cited study.

| Publication | Study and findings | Limits and implication for EvidenceTrail |
| --- | --- | --- |
| **Büchter et al. (2023).** [Systematic reviewers used various approaches to data extraction and expressed several research needs: a survey.](https://pubmed.ncbi.nlm.nih.gov/37286149/) *Journal of Clinical Epidemiology*, 159, 214–224. DOI: [10.1016/j.jclinepi.2023.05.027](https://doi.org/10.1016/j.jclinepi.2023.05.027). PMID: 37286149. | A 2022 online survey of 162 reviewers found widespread spreadsheet use (83%). Adapted or newly developed extraction forms were more common than generic forms. Respondents identified error reduction and extraction-support tools as research needs. | A self-selected survey does not represent every review team. **Implication:** accommodate existing column names and provide clear templates; avoid assuming that every project uses the same questions. |
| **Tang et al. (2025).** [Effects of double data extraction on errors in evidence synthesis: a crossover, multicenter, investigator-blinded, randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/39764599/) *Postgraduate Medical Journal*, 101(1197), 603–611. DOI: [10.1093/postmj/qgae195](https://doi.org/10.1093/postmj/qgae195). PMID: 39764599. | In a crossover trial, 100 participants extracted binary adverse-outcome data from pharmaceutical and non-pharmaceutical trials. Cross-checking reduced errors, but substantial errors remained afterward. | The task was restricted to binary adverse outcomes. Reported study-level error rates must not be described as cell-level rates or universal estimates. **Implication:** help reviewers compare answers and return to the sources; agreement alone is insufficient evidence of correctness. |
| **Afifi, Stryhn and Sanchez (2023).** [Data extraction and comparison for complex systematic reviews: a step-by-step guideline and an implementation example using open-source software.](https://pmc.ncbi.nlm.nih.gov/articles/PMC10691069/) *Systematic Reviews*, 12, 226. DOI: [10.1186/s13643-023-02322-1](https://doi.org/10.1186/s13643-023-02322-1). PMID: 38041161. | A methodological guideline and Epi Info/R implementation describe data dictionaries, validation, piloting, exports, comparison, and adjudication. The paper emphasizes defining what each row represents and comparing manageable batches. | This is a worked methods proposal, not an effectiveness trial. **Implication:** define record identifiers clearly, retain source information, and make unresolved differences visible. Repeated report IDs can be legitimate when a table has multiple extracted fields per report. |
| **Gartlehner et al. (2025).** [Artificial Intelligence-Assisted Data Extraction With a Large Language Model: A Study Within Reviews.](https://pmc.ncbi.nlm.nih.gov/articles/PMC13091441/) *Annals of Internal Medicine*, 178(12), 1763–1771. DOI: [10.7326/ANNALS-25-00739](https://doi.org/10.7326/ANNALS-25-00739). PMID: 41183336. | A prospective comparison across six ongoing reviews included 63 studies and 9,341 data elements. AI-assisted extraction with human verification had 91.0% accuracy, versus 89.0% for the human-only process. Omissions were the most common error. | Comparisons were exploratory. Adjudicating only disagreements could miss errors shared by both approaches. **Implication:** display completeness and verification separately; do not equate concordance, a recorded review status, or a clean audit with scientific accuracy. |
| **Jansen et al. (2025).** [Data extraction by generative artificial intelligence: Assessing determinants of accuracy using human-extracted data from systematic review databases.](https://pubmed.ncbi.nlm.nih.gov/41396533/) *Psychological Bulletin*, 151(10), 1280–1306. DOI: [10.1037/bul0000501](https://doi.org/10.1037/bul0000501). PMID: 41396533. | Eight models extracted 312,329 data points across 2,179 studies and 186 variables. Accuracy varied most by variable. Context variables were more accurate than variables used for effect-size calculation; detailed variable descriptions were associated with better accuracy. | Existing human-extracted databases supplied the comparison data. Associations do not establish that a particular interface improves accuracy. **Implication:** make field definitions clear and show field-specific problems instead of one overall quality score. |
| **Konet et al. (2024).** [Performance of two large language models for data extraction in evidence synthesis.](https://pubmed.ncbi.nlm.nih.gov/38895747/) *Research Synthesis Methods*, 15(5), 818–824. DOI: [10.1002/jrsm.1732](https://doi.org/10.1002/jrsm.1732). PMID: 38895747. | A comparison using ten articles found that PDF processing affected performance substantially. Many errors in one model workflow arose from its PDF plugin; performance improved when selected text was supplied. | The sample was small, prompts were developed using one model, and training-data overlap was unknown. These are historical model results. **Implication:** any future PDF feature must expose parsing failures and source text; reliable file ingestion cannot be assumed. |

Together, these sources support attention to the extraction process and its records. They do not support a claim that a passing spreadsheet audit validates the underlying science, or that AI can replace source verification across review types.

## Official guidance and existing workflows

| Source | Relevant guidance or documented behavior | How we use it |
| --- | --- | --- |
| [Cochrane Handbook, Chapter 5: Collecting data](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05), especially §§5.4.3 and 5.5.2–5.5.5. The page cites Handbook version 6.5 (2024); the chapter itself was last updated in October 2019. | Recommends piloting forms, independent duplicate extraction, and a predefined approach to disagreements. Its standards distinguish mandatory duplicate outcome extraction from highly desirable duplicate extraction of study characteristics. | Comparison and decision records can support a team's chosen method. They do not establish adherence to every Cochrane standard. |
| [JBI Manual for Evidence Synthesis (2024)](https://jbi-global-wiki.refined.site/download/attachments/355599504/JBI%20Manual%20for%20Evidence%20Synthesis%202024.pdf), §10.2.7, PDF page 170. | Scoping-review charting instruments may be adapted and refined. The manual suggests trying the form on two or three sources with at least two team members; other approaches may be considered when this is infeasible, with transparent reporting. | Preserve clear definitions and pilot the workflow with the review team. Referencing JBI guidance is not JBI certification or endorsement of the app. |
| Covidence: [comparison and consensus in Extraction 1](https://support.covidence.org/en/help/comparison-and-consensus) and [Extraction 2](https://support.covidence.org/help/consensus-9831e0af), updated August 16 and August 14, 2026, respectively. | Official documentation describes retaining reviewer responses, identifying differences, and selecting or entering a final answer. Extraction 2 also displays reviewer comments during consensus. | These workflows already exist in established software. EvidenceTrail's aim is an accessible spreadsheet companion, not a claim to have invented reviewer comparison. Vendor documentation is not an independent validation study. |

## Development decisions

The table records the priorities implemented for this expansion and explains their purpose. The [README](../README.md) and [change log](../CHANGELOG.md) describe the released capabilities and their limits.

| Priority | Purpose | Boundary to preserve |
| --- | --- | --- |
| Map uploaded columns to EvidenceTrail fields | Reduce the need to rename an existing table before trying an audit. | Mapping column names does not translate a study's concepts or resolve incompatible definitions. |
| Summarize review status and completeness | Show where records lack expected information or remain under review. | A status count is a workflow summary. It is not an accuracy estimate or a measure of the strength of evidence. |
| Compare two reviewer spreadsheets | Identify missing records and different field values while retaining each submitted answer. | A text difference can be harmless wording variation. Matching values can share an error. Ambiguous record identifiers need correction before reliable matching. |
| Record reasoned decisions and export the log | Make it possible to see the submitted values, the chosen resolution, and the reason supplied by a reviewer. | The researcher makes the decision. An exported log is not a multi-user, tamper-proof audit system. |
| Preserve original input and its provenance | Keep comparisons and reports connected to the inputs used for that run. | A file fingerprint identifies file contents; it does not verify the source publication, extraction, or interpretation. |

The current table model has **one row per extracted field**, with a unique `record_id`. A `report_id` can appear in several rows. Report counts, extraction-row counts, and unique-study counts should therefore remain separate. More general row structures and configurable validation schemas belong in future work.

## Existing tools and approaches

These are alternatives or companions, not a ranking. This review did not compare prices, usability, privacy practices, or effectiveness across products.

| Approach | Where it may fit | Evidence boundary |
| --- | --- | --- |
| **Covidence** | Teams wanting an established review environment with documented comparison and consensus workflows. | The official [Extraction 1](https://support.covidence.org/en/help/comparison-and-consensus) and [Extraction 2](https://support.covidence.org/help/consensus-9831e0af) guides describe these functions. No superiority claim is made. |
| **REDCap** | Institution-managed collection forms and databases where structured fields, user activity records, and exports are useful. | The [official software overview](https://projectredcap.org/software/) describes data dictionaries, audit trails, and exports. Whether a local installation meets a project's requirements depends on its configuration and governance. |
| **Epi Info with R — historical implementation** | A worked example of linked extraction tables and scripted comparison, useful for understanding the methods. | Afifi et al. describe a [2023 implementation](https://pmc.ncbi.nlm.nih.gov/articles/PMC10691069/), not a controlled tool comparison. [CDC reports](https://www.cdc.gov/epiinfo/index.html) that Epi Info development and technical assistance stopped in September 2025. Its statement that the desktop version remained operational on Windows 11 refers to September 2025. This is not a recommendation to adopt a currently supported platform. |
| **Structured spreadsheets with version control** | Small teams that already work in tables and can maintain a shared dictionary, stable identifiers, and documented revisions. | This is a practical design option informed by the survey and methods literature, not a validated intervention. File history alone does not establish who checked a source or why a decision changed. |

EvidenceTrail can occupy a narrower role: inspect an existing table and make review work easier to carry forward. It does not need to replace an institution's review or data-management platform.

## What to evaluate next

A small user pilot should precede claims about research benefits. Use synthetic tables with known planted issues and openly available tables that can legally be reused. Include people with different levels of review experience and ask them to:

1. Map an unfamiliar table and explain what each field represents.
2. Identify planted omissions, duplicate record identifiers, and reviewer differences.
3. Inspect a source location and document a reasoned resolution.
4. Export the results and reconstruct which inputs and decisions produced them.

Record time to identify planted issues, missed issues, unnecessary flags, mapping mistakes, and problems interpreting the interface. Ask whether the exported record is understandable to a second researcher. If outcomes are compared with a spreadsheet-only workflow, define the tasks, reference answers, and analysis before collecting results.

These would be **future evaluation results**. Automated software tests and a successful demonstration show that specified behavior works on tested examples; they do not demonstrate reduced extraction errors in real reviews.

Further development could add configurable validation schemas, support for additional row structures, and independently evaluated PDF or AI assistance. Any such feature should retain the original evidence, make failures visible, and allow human correction. Real-world validation, privacy review for the intended hosting environment, and accessibility testing remain separate work.
