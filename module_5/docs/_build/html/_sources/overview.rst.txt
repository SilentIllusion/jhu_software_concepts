Overview & Setup
================

Quick start
-----------

1. Create and activate a virtual environment (optional but recommended)::

     python -m venv .venv
     .venv\Scripts\activate  # Windows

2. Install dependencies::

     pip install -r module_4/requirements.txt

3. Set database connectivity:

   * Default code uses ``dbname=grad_cafe``, user ``postgres``, password ``04021986`` on localhost.
   * You can override by exporting ``DATABASE_URL`` in the standard libpq format, or by updating ``get_db_connection`` in ``run.py`` / ``query_data.py``.

4. Run the Flask app::

     python module_4/src/run.py

   The server listens on ``0.0.0.0:8080``.

Running tests
-------------

Execute the full suite with coverage::

   python -m pytest module_4 -m "web or buttons or analysis or db or integration"

Coverage output is written to ``module_4/.coverage`` and a summary to ``module_4/coverage_summary.txt`` when redirected.

Environment variables
---------------------

* ``DATABASE_URL`` (optional): libpq-style URI to override default PostgreSQL settings.
* ``SYNC_PULL_DATA`` (tests use ``True`` to avoid threads): set to ``1`` to run pulls synchronously in-process.
