# EvidenceTrail

**A small research tool for checking extraction tables before the next review step.**

EvidenceTrail helps researchers inspect extraction tables, compare two reviewers' records, and document the decisions that follow. It finds missing source locations, inconsistent status labels, duplicate record IDs, and recorded disagreements, then turns those checks into downloadable reports.

This is an early working prototype, version **0.2.0**. The included examples contain synthetic records. EvidenceTrail checks table structure and consistency; scientific accuracy still requires reviewing the sources.

![EvidenceTrail displaying the five issues in its synthetic demonstration](docs/images/demo.jpg)

## Why this project exists

Evidence extraction involves more than copying an answer into a spreadsheet. A useful record also needs a clear connection to a report, an honest account of what the source says, and a way to track review. Small inconsistencies in those records can make later synthesis harder.

EvidenceTrail makes a first pass at those inconsistencies visible. A researcher still decides what needs correction and verifies the evidence against the source.

## What the prototype does

- Reads extraction tables, with explicit mapping from your column names to seven required fields.
- Checks identifiers, status labels, values, and source locations, with explanations and suggested next steps.
- Summarizes recorded review progress and evidence completeness by extraction field.
- Compares two reviewer tables by report and field, keeping differences in answers separate from differences in source locations.
- Records your choice, name or identifier, and reason for a reviewer decision, while preserving both submitted answers.
- Exports findings and reviewer decision records with input-file fingerprints and other provenance. The Python app also provides an audit ZIP bundle.
- Includes a 20-row demonstration with five planted findings, a clean table, a blank template, and paired reviewer examples.

There are two ways to use EvidenceTrail:

| | Browser demo | Full Python app |
| --- | --- | --- |
| Input | CSV | CSV or an Excel `.xlsx` sheet |
| Checks, column mapping, progress and field summaries | Yes | Yes |
| Reviewer comparison and decision CSV/JSON | Yes | Yes |
| Audit ZIP bundle | No | Yes |
| Processing | In your browser; selected file contents are not uploaded | On the machine running the Python app |
| Setup | Static site, designed for GitHub Pages | Local Python installation |

Both versions leave your input files unchanged and use temporary working state. Each file can be up to **5 MiB**, with up to **10,000 data rows** and **50 columns**. In the Python app, Excel workbooks also have a 25 MiB limit on expanded contents, and the selected sheet must contain values rather than formulas.

The [hosting guide](docs/deployment.md) describes publishing the browser demo from this repository with GitHub Pages. No Streamlit account or separate application host is needed for that route. See [getting started](docs/getting-started.md) for the differences between versions.

## Run the full app locally

You need Python **3.10 or later** and Git. Open a terminal, then run:

```sh
git clone https://github.com/TheThunda01/evidencetrail.git
cd evidencetrail
python -m venv .venv
```

If your system uses the command `python3`, use `python3 -m venv .venv` for that last step.

Activate the environment on macOS or Linux:

```sh
source .venv/bin/activate
```

Or in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then install the dependencies and start the app:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local address printed in the terminal. The [getting-started guide](docs/getting-started.md) walks through the demo and your first audit.

The **Audit a table** workspace opens with **Demo with five issues** selected. Review the findings, compare the **Clean example**, or choose **Upload a file** to check your own table. The [demo's expected-findings file](examples/expected_findings.json) records the deliberately planted issues.

## Table format

Use **one row per extracted field**. Each row has its own `record_id`; several rows can share a `report_id` when they describe the same report.

| Required column | Purpose |
| --- | --- |
| `record_id` | A unique identifier for this extraction row. |
| `report_id` | The identifier of the report being described. |
| `field` | The question or attribute being extracted. |
| `value` | The extracted answer, when available. |
| `evidence_status` | Whether and how the source supports an answer. |
| `source_locator` | A page, section, table, figure, or other location in the source. |
| `review_status` | The current review state of the row. |

Your source columns can have different names: map each one to its role in the app. Mapping changes column names in a working copy, not cell values or status labels. Optional columns include `reviewer`, `notes`, and `source_url`. Start with [the blank CSV template](examples/extraction_template.csv), and see the [data dictionary](docs/data-dictionary.md) for allowed labels and examples.

For reviewer comparison, each combination of `report_id` and `field` must occur once in each table. The reviewers' `record_id` values can differ. Missing or ambiguous comparison keys are blocked rather than paired automatically.

## What a finding means

A finding is a reason to inspect a record. For example, a row marked `Reported` with no source location needs a source check. A duplicated `record_id` needs a decision about the identifiers or the rows. A `Disagreement` needs researcher review.

Findings distinguish required table corrections from missing supporting information and disagreements. Downloads label these categories `error` and `review`; neither label is a judgment of scientific accuracy. The browser shows explanations and next steps in its findings table. In the Python app, choose **Inspect a finding** for those details.

**Zero findings means only that these checks found no issues.** A table can pass every check and still contain an incorrect extraction, an incomplete source location, or a mistaken interpretation. Likewise, `Verified` is a status supplied by the researcher, not a certification from the app.

The [methods and limitations](docs/methods-and-limitations.md) explain exactly what the checks cover.

## Compare reviewers and record decisions

Choose **Compare reviewers** and load the reviewer demo: **Load reviewer demo** in each browser panel, or **Demo reviewers** in the Python app. The underlying [reviewer_a.csv](examples/reviewer_a.csv) and [reviewer_b.csv](examples/reviewer_b.csv) contain 19 comparable pairs: 17 agree on answer and evidence status, and two differ. Each table also has one unmatched record. Two matched pairs use different source locations.

For a matched pair, you can use either reviewer's answer, enter a different answer, or defer the decision. Each saved decision needs a reviewer name or identifier and a reason. Saving again for the same pair replaces its current decision in the session. Download a copy before clearing the session or leaving the app; it is not a persistent research database or an append-only history.

Decisions do not alter the source tables or automatically mark their rows as `Verified`. A recorded decision is your documented choice, not source verification performed by the app.

## Data handling

Both versions keep working data and current reviewer decisions in memory. They do not fetch source links or send records to an external analysis service. Downloaded files are saved wherever you choose in your browser.

The Python app's audit ZIP excludes the original upload and extracted answer values, but includes record IDs, field labels, source filenames, mappings, and other audit metadata. The browser audit JSON also contains identifiers and field summaries. Reviewer comparison and decision downloads include the submitted answers and locators. Inspect exports before sharing them.

In the **browser demo**, selected CSV contents and decisions stay in browser memory. The demo does not transmit them, use a backend database, save them to browser storage, or load code from a third-party CDN. GitHub still receives normal requests for the page and its assets; its hosting documentation describes [visitor IP logging](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages#data-collection).

In the **Python app**, processing occurs on the machine running it. A local session uses your computer; a separately hosted instance sends uploaded files to that host, where administrators and infrastructure may have access to runtime data. The repository examples are synthetic; do not add participant data or confidential research records to the public repository. Neither version is a persistent research repository.

## Check the code

Run the Python checks from the project directory:

```sh
python -m unittest discover -s tests -v
```

For the browser core, use Node.js 22 or later:

```sh
node --test tests/web-core.test.mjs
```

The browser parity tests compare known examples with the Python implementation. They check software behavior, not effectiveness in real reviews. For ways to help, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Research basis and next steps

The [research review](docs/research-review-2026-10-13.md) explains the scientific and practical guidance behind the expansion, including where established tools already address these needs. This is an evidence-informed design, not a validated intervention.

Future work could add configurable validation schemas, additional table structures, and carefully evaluated PDF or AI assistance. A user pilot should assess mapping usability and how people find and resolve known issues before claims are made about research benefits.

See [CHANGELOG.md](CHANGELOG.md) for the version history.

## Reuse and citation

The code is available under the [MIT license](LICENSE). If you use EvidenceTrail in research, the repository includes [citation metadata](CITATION.cff). Record the version you used so others can identify the same implementation.
