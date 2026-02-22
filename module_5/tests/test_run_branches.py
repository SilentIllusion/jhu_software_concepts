"""Additional branch coverage tests for run.py helpers and routes."""

import types

import pytest

import run


@pytest.mark.db
def test_get_db_connection(monkeypatch):
    """get_db_connection forwards to psycopg.connect with defaults."""
    sentinel = object()
    monkeypatch.setattr(run.psycopg, "connect", lambda **kwargs: sentinel)
    assert run.get_db_connection() is sentinel


@pytest.mark.db
def test_get_db_connection_env(monkeypatch):
    """Environment DATABASE_URL is honored."""
    sentinel = object()
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setattr(run.psycopg, "connect", lambda url=None, **kwargs: sentinel if url == "postgresql://example" else None)
    assert run.get_db_connection() is sentinel


@pytest.mark.db
def test_query_scalar_params_and_none():
    """query_scalar handles params and None result rows."""
    class Cur:
        def __init__(self):
            self.calls = []
            self.rows = [None]

        def execute(self, sql, params=None):
            self.calls.append((sql, params))

        def fetchone(self):
            return self.rows.pop(0)

    cur = Cur()
    assert run.query_scalar(cur, "SELECT 1", ("x",)) is None
    assert cur.calls[0] == ("SELECT 1", ("x",))


@pytest.mark.db
def test_insert_entries_empty_and_duplicate():
    """Insert helper skips empty input and dedupes URLs within batch."""
    class Cur:
        def __init__(self, conn):
            self.conn = conn
            self.data = []

        def executemany(self, sql, data):
            self.data.extend(data)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class Conn:
        def __init__(self):
            self.cur = Cur(self)
            self.commits = 0

        def cursor(self):
            return self.cur

        def commit(self):
            self.commits += 1

    conn = Conn()
    assert run._insert_entries(conn, []) == 0

    rows = [
        {"url": "u1", "program": "p1"},
        {"url": "u1", "program": "p2"},
    ]
    inserted = run._insert_entries(conn, rows)
    assert inserted == 1
    assert len(conn.cur.data) == 1


@pytest.mark.buttons
def test_run_scrape_job_running_flag(monkeypatch):
    """Early return when a scrape job is already running."""
    run.scrape_state["running"] = True
    run.scrape_state["message"] = None
    run._run_scrape_job()
    # Ensure running flag reset path not triggered because early return
    assert run.scrape_state["running"] is True


@pytest.mark.buttons
def test_run_scrape_job_exception(monkeypatch):
    """Failure in scrape job sets failure message and clears running flag."""
    run.scrape_state["running"] = False
    monkeypatch.setattr(run, "get_db_connection", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    run._run_scrape_job()
    assert "failed" in (run.scrape_state["message"] or "").lower()
    assert run.scrape_state["running"] is False


@pytest.mark.buttons
def test_pull_data_async_path(monkeypatch):
    """When SYNC_PULL_DATA is false the endpoint spawns a background thread."""
    started = {"thread": False}

    class FakeThread:
        def __init__(self, target=None, daemon=None):
            self.target = target
            started["daemon"] = daemon

        def start(self):
            started["thread"] = True

    monkeypatch.setattr(run.threading, "Thread", FakeThread)
    monkeypatch.setattr(run, "_run_scrape_job", lambda: None)

    app = run.create_app({"TESTING": True, "SYNC_PULL_DATA": False})
    client = app.test_client()
    resp = client.post("/pull-data")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
    assert started["thread"] is True


@pytest.mark.analysis
def test_format_two_decimals_none():
    """Formatting helper returns None when input is None."""
    assert run._format_two_decimals(None) is None
