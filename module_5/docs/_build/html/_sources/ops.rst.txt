Operational Notes
=================

Busy-state policy
-----------------

* ``/pull-data`` sets ``scrape_state["running"]`` while a job is active; ``/update-analysis`` returns HTTP 409 + ``{"busy": true}`` when a pull is in progress.
* Tests can flip ``SYNC_PULL_DATA=True`` to run pulls synchronously without threads.

Idempotency & uniqueness
------------------------

* Rows are deduped in-memory on URL before insert. ``admission_results.url`` should be unique in the DB to enforce at the storage layer.
* ``scrape_new_data`` also skips URLs already present.

Selectors for UI tests
----------------------

* Pull button: ``data-testid="pull-data-btn"``
* Update button: ``data-testid="update-analysis-btn"``

Troubleshooting
---------------

* ``DATABASE_URL`` not set: the app falls back to local ``grad_cafe`` database; ensure Postgres is running locally or provide a URL.
* Coverage missing modules: ensure `pytest.ini` is picking up ``module_4/src`` and that `.coveragerc` points to ``module_4/.coverage``.
* Busy errors (409): wait for the running job to finish or clear ``scrape_state["running"]`` in tests via fixtures.
