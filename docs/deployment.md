# Publishing the browser demo

EvidenceTrail's browser demo is a static HTML, CSS, and JavaScript site. It can be published from this repository with **GitHub Pages**. No Streamlit account, Python server, database, API key, or separate hosting account is needed for this version.

The browser demo accepts CSV files. The full Python app remains available for Excel input and audit ZIP exports; see the [local setup instructions](../README.md#run-the-full-app-locally).

## GitHub Pages settings

In the repository's **Settings → Pages**, use:

| Setting | Value |
| --- | --- |
| Source | Deploy from a branch |
| Branch | `main` |
| Folder | `/docs` |
| Entry page | `docs/index.html` |
| Jekyll processing | Disabled by `docs/.nojekyll` |

Save the publishing source, then inspect the Pages deployment in the repository's Actions history. GitHub's [publishing-source guide](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) explains the branch and folder settings. The person configuring Pages needs suitable repository permissions.

Keep all referenced site assets in `docs/` and use relative asset paths so the site works under a project URL. Do not put private files in the published folder. The live address shown by GitHub should be added to the README only after the deployed interface has been checked. A passing workflow or an HTTP response alone does not establish that its controls work.

## Preview and checks

To preview the static files locally from the repository root:

```sh
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000` in a browser. Serving the files over HTTP allows browser modules and example files to load correctly.

Run the browser-core checks with Node.js 22 or later:

```sh
node --test tests/web-core.test.mjs
```

Also run the Python checks when changing shared behavior or the full app:

```sh
python -m unittest discover -s tests -v
```

The browser parity checks compare defined examples with Python behavior. They are software checks, not a real-world validation study.

## Verify the deployed interface

1. Open the public page without a signed-in hosting session.
2. Run the synthetic audit demo. It should show 20 rows, two error findings, and three items for review.
3. Run the clean example. It should show no audit findings and 20 pending review records.
4. Compare the reviewer examples. Expect 19 comparable pairs, 17 agreements, two differences, one first-only record, one second-only record, and two locator changes.
5. Select a CSV with different column names, complete the mapping, and run its audit. Check that no request sends the selected file's contents to a server.
6. Record a clearly labelled test decision. Download its CSV and JSON, and inspect the decision, rationale, source fingerprints, and mappings.
7. Clear the session and confirm that loaded sources, results, and decisions are removed from the page. Refresh and confirm that they do not return from browser storage.

Only CSV is supported in this deployment. Excel workbooks and audit ZIP bundles belong to the Python app and should not be advertised as browser features.

## Data handling

The page reads selected CSV files and holds working data in browser memory. It does not send their contents to GitHub or an analysis service, use a backend database, or persist records in browser storage. Scripts and styles are supplied with the site; no third-party CDN or AI service is required. Ordinary page and asset requests still go to the static host. GitHub documents [visitor IP logging](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages#data-collection).

Downloads are created in the browser and may contain research records, reviewer names, and rationales. The audit JSON includes identifiers and field summaries; it is not an anonymized artifact. Clearing the page does not delete downloaded files or change the host's ordinary access records.

For the Python app, uploaded files are processed on the machine running the application. That is a different architecture: a remotely hosted Python instance receives the upload. Its infrastructure needs its own assessment before confidential use.

## Updates

Changes pushed to `main` are published from `docs/`. Check the Pages workflow, inspect the live version, and repeat relevant interface checks after changing the site. Keep the README link and screenshots aligned with what visitors can actually use.
