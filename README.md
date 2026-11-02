# US Election Results · 2026

A responsive, static dashboard for **435 House, 35 Senate and 36 state governor races**, with 50 state drilldowns. No sample vote totals, candidate names or winners ship in the public snapshot.

**Coverage is partial, not a nationwide live feed.** One official adapter (Minnesota) is implemented. It will not import before November 3 at 8 p.m. Central and rejects test results. The verified November 2 source page still says **Test Results**. North Carolina download research is documented, but its adapter is not implemented. The remaining states and AP/CNN/Fox feeds are not connected. The UI makes these limits visible. Cloudflare hosting and the scheduled job must be activated by the repository owner.

## Run locally

Python 3.12+ and Node 22+:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/validate.py
python -m unittest discover -s tests -p 'test_*.py'
npm test
npm run build
python -m http.server 4173 --directory dist
```

Open `http://localhost:4173`. Office and state selection are shareable, for example `/#office=senate&state=MN`. No frontend dependencies, accounts, analytics, cookies or API keys are required.

## Architecture

```text
Official state endpoint -> identity/test-mode checks -> raw SHA-256 archive
    -> state adapter -> schema + integrity validation -> atomic JSON snapshot
Editorial evidence (separate news calls/certifications) ------^
    -> GitHub data commit -> Cloudflare Pages -> static browser dashboard
```

- `public/`: HTML, CSS, browser modules and published JSON. Never put credentials here.
- `scripts/catalog.py`: sourced race inventory, not results; excludes delegates/territories, primaries, runoffs and other House special elections.
- `scripts/pipeline.py`: retry-limited collection, source checks, raw audit artifacts, normalization, last-good retention and atomic writes.
- `schema/results.schema.json`: closed Draft 2020-12 contract; `scripts/validate.py` adds source, inventory, totals and reference checks.
- `config/sources.json`: approved source identity and enabled adapters; `config/editorial.json`: reviewed evidence records.
- `docs/workflows/`: ready-to-install GitHub Actions validation and opt-in collection templates. The available Git token cannot upload files under `.github/workflows/`; the owner must install these templates as described in the deployment guide. Tests use **synthetic fixtures only**, which never enter `public/` or `dist/`.

The initial snapshot has `official: null` for every race. This means **not imported**, not zero votes, polls closed or no election. The dashboard has no chamber-control projection: non-contested Senate seats and governorships are not silently added to results. A candidate leading in votes is never labeled the winner. Source-file timestamps and retrieval timestamps remain distinct; stale data is labeled after 30 minutes. Browser refresh is every 60 seconds while visible; collection is a separate, best-effort 15-minute job.

## Operate the pipeline

```sh
python scripts/pipeline.py
python scripts/validate.py
npm run build
```

The pipeline returns nonzero on enabled-source failure, retains that source's previous validated totals, and writes an error into `public/data/health.json`. The workflow publishes health and retained data before marking the run failed. A completely invalid final snapshot is never written. Raw responses and provenance manifests are archived in `work/raw/` and retained as GitHub workflow artifacts for 30 days. Git commits preserve published snapshots. Save artifacts elsewhere if you need longer retention.

Minnesota ingestion requires the correct 2026 production status page, exact linked download URLs, all 10 supported contests, the documented 16-field format, consistent totals and unique candidate IDs. It checks the status page before and after downloading. It rejects regressing source timestamps but allows legitimate downward vote corrections. HTTP Last-Modified is a **source file timestamp**, not a claim about when an individual ballot was counted. Counts never create news calls or certification.

For a new state: verify an official 2026 endpoint and its production/test signal, add an allowlisted source, implement an adapter, add isolated fixtures and failure tests, then enable it. Never infer a live endpoint by changing a year in a historical URL. Do not turn on the North Carolina entry until its adapter and production verification exist.

See [data contract](docs/DATA.md), [source research](docs/SOURCES.md), and [Cloudflare deployment](docs/DEPLOYMENT.md).
