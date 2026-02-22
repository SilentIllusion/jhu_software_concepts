# Module 4 – Grad Café Analytics (Stabilized & Tested)

## What’s in this module
- `src/run.py` — Flask app factory, routes (`/analysis`, `/pull-data`, `/update-analysis`), busy-state gating, DB inserts, and analysis aggregation.
- `src/query_data.py` — All SQL used by the web layer and CLI helpers; DB connection now honors `DATABASE_URL`.
- `src/scripts/scrape.py` — Grad Café scraper, parsing helpers, save helper (defaults to `module_4/applicant_data.json`).
- `src/scripts/clean.py` — Normalization, HTML stripping, persistence helper (defaults to `module_4/applicant_data.json`).
- `src/load_data.py` — Bulk loader for `corrected_application_data_v2.json` into `admission_results`.
- `src/templates/`, `src/static/` — UI for Analysis page with stable `data-testid` selectors.
- `tests/` — Full pytest suite with markers (`web`, `buttons`, `analysis`, `db`, `integration`) and 100% coverage.
- `docs/` — Sphinx docs (RTD theme) with overview, architecture, API autodoc, testing guide, and ops notes.
- `.github/workflows/tests.yml` — CI to start Postgres and run pytest.
- `.readthedocs.yaml` — RTD build config targeting `module_4/docs/conf.py`.

## Setup
```bash
pip install -r module_4/requirements.txt
```
Dependencies include Flask, psycopg, BeautifulSoup, urllib3, pytest/pytest-cov, and Sphinx + RTD theme.

## Run the app
```bash
python module_4/src/run.py
```
Server listens on `0.0.0.0:8080`. Configure DB via `DATABASE_URL`; otherwise falls back to local `grad_cafe` as user `postgres`.

## Run tests
```bash
python -m pytest module_4 -m "web or buttons or analysis or db or integration"
```
Coverage data is written to `module_4/.coverage` (see `.coveragerc`). Current coverage: 100%.

## Sphinx docs
Build locally:
```bash
cd module_4/docs
sphinx-build -b html . _build/html
```
Open `_build/html/index.html` to view. RTD config provided via `.readthedocs.yaml`.

## Behavior highlights
- Busy-state gating: `/pull-data` and `/update-analysis` return 409 JSON when a pull is running; otherwise `/pull-data` returns `{"ok": true}`.
- Stable UI selectors: `data-testid="pull-data-btn"` and `data-testid="update-analysis-btn"`.
- Percentages formatted to two decimals; analysis page renders required “Answer:” labels.
- Idempotent inserts: duplicates (by URL) are skipped in `_insert_entries` and `scrape_new_data`.

## Data files
- `module_4/corrected_application_data_v2.json` — seed data for loader.
- `module_4/applicant_data.json` — default output for scrape/clean save helpers.

## CI
- GitHub Actions workflow: `.github/workflows/tests.yml` spins up Postgres and runs the marked pytest suite with coverage enforcement.
- RTD build uses `.readthedocs.yaml`.
