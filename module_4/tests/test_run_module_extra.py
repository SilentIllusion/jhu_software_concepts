import runpy
import sys
import types

import pytest


@pytest.mark.db
def test_run_helper_branches(monkeypatch):
    from src.app import run

    sentinel = object()
    monkeypatch.setattr(run.psycopg, "connect", lambda **kwargs: sentinel)
    assert run.get_db_connection() is sentinel

    class Cur:
        def __init__(self):
            self.calls = []
            self.rows = [None, (7,)]

        def execute(self, sql, params=None):
            self.calls.append((sql, params))

        def fetchone(self):
            return self.rows.pop(0)

    cur = Cur()
    assert run.query_scalar(cur, "q1") is None
    assert run.query_scalar(cur, "q2", (1,)) == 7
    assert run._format_two_decimals(None) is None
    assert run._insert_entries(type("Conn", (), {"cursor": lambda self: None})(), []) == 0


@pytest.mark.db
def test_insert_entries_duplicate_branch(monkeypatch):
    import run

    class DummyCursor:
        def executemany(self, sql, data):
            self.data = data

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyConn:
        def __init__(self):
            self.cur = DummyCursor()

        def cursor(self):
            return self.cur

        def commit(self):
            return None

    conn = DummyConn()
    rows = [
        {"url": "u1", "program": "p"},
        {"url": "u1", "program": "p2"},
    ]
    inserted = run._insert_entries(conn, rows)
    assert inserted == 1


@pytest.mark.buttons
def test_run_async_and_error_paths(monkeypatch):
    import run

    class T:
        def __init__(self, target=None, daemon=None):
            self.started = False

        def start(self):
            self.started = True

    monkeypatch.setattr(run.threading, "Thread", T)

    app = run.create_app({"TESTING": True, "SYNC_PULL_DATA": False})
    client = app.test_client()
    r = client.post("/pull-data")
    assert r.status_code == 302

    run.scrape_state["running"] = True
    run._run_scrape_job()
    run.scrape_state["running"] = False

    monkeypatch.setattr(run, "get_db_connection", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    run._run_scrape_job()
    assert "Pull Data failed" in (run.scrape_state["message"] or "")


@pytest.mark.web
def test_run_module_main_exec(monkeypatch):
    fake_psycopg = types.SimpleNamespace(connect=lambda **kwargs: object())
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)

    import flask

    monkeypatch.setattr(flask.Flask, "run", lambda self, **kwargs: None)
    runpy.run_module("run", run_name="__main__")
