Testing Guide
=============

How to run
----------

Full suite with coverage (marks enforced)::

   python -m pytest module_4 -m "web or buttons or analysis or db or integration"

Common selections
-----------------

* Web/HTML checks: ``-m web``
* Button/busy behavior: ``-m buttons``
* Analysis formatting: ``-m analysis``
* DB CRUD: ``-m db``
* End-to-end: ``-m integration``

Fixtures & doubles
------------------

* ``run_module`` (conftest): builds a test Flask app with ``SYNC_PULL_DATA=True`` and injects a fake psycopg connection.
* ``sample_entries``: two canonical applicant rows used across DB/ETL tests.
* ``FakeConnection`` / ``FakeCursor``: lightweight in-memory DB stand-ins recording SQL and rows.

Coverage artifacts
------------------

* Coverage data: ``module_4/.coverage`` (configured via ``.coveragerc``).
* Summary (when redirected): ``module_4/coverage_summary.txt``.

