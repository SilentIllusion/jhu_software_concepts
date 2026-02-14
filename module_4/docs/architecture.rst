Architecture
============

Layers
------

* Web (Flask) — ``run.py`` defines the application factory and routes. The ``/analysis`` page renders metrics and exposes ``/pull-data`` and ``/update-analysis`` actions with busy-state gating.
* ETL (Scraping/Cleaning) — ``scripts/scrape.py`` pulls Grad Cafe listings; ``scripts/clean.py`` normalizes fields and removes HTML/noise; ``load_data.py`` bulk-loads the corrected seed JSON into the database.
* Data / DB access — ``query_data.py`` holds SQL used by both the web layer and CLI helpers; ``run.py`` uses these queries to compute dashboard answers. Database calls rely on ``psycopg`` and default to the local Postgres instance.

Data flow
---------

1. ``/pull-data`` triggers ``scrape_new_data`` to fetch new rows, then ``clean_data`` to normalize them.
2. ``_insert_entries`` in ``run.py`` writes cleaned rows into ``admission_results`` (idempotent by URL).
3. ``/analysis`` reads aggregated metrics via SQL in ``query_data.py`` and renders them with Jinja templates.

Concurrency & state
-------------------

* A module-level ``scrape_state`` dict tracks whether a pull is running and holds status messages.
* ``scrape_lock`` prevents concurrent pulls and gates ``/update-analysis`` when busy.

Files of interest
-----------------

* ``src/run.py`` — Flask app, routes, threading logic, DB insertion.
* ``src/scripts/scrape.py`` — HTTP scraping, parsing helpers, new-data scanning.
* ``src/scripts/clean.py`` — HTML stripping, normalization, persistence helpers.
* ``src/load_data.py`` — One-off loader for the corrected JSON seed.
* ``src/query_data.py`` — SQL strings and small DB helper.
