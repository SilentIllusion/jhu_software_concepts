"""Tests for lightweight helpers in query_data."""

import pytest

import query_data


@pytest.mark.db
def test_get_db_connection(monkeypatch):
    """get_db_connection forwards to psycopg.connect with defaults."""
    sentinel = object()
    monkeypatch.setattr(query_data.psycopg, "connect", lambda **kwargs: sentinel)
    assert query_data.get_db_connection() is sentinel


@pytest.mark.db
def test_query_scalar(monkeypatch):
    """query_scalar executes SQL and returns the first column of one row."""
    calls = []

    class Cur:
        def __init__(self):
            self.rows = [(5,), None, (None,)]

        def execute(self, sql, params=None):
            calls.append((sql, params))

        def fetchone(self):
            return self.rows.pop(0) if self.rows else None

    cur = Cur()
    assert query_data.query_scalar(cur, "SELECT 1") == 5
    assert calls[0] == ("SELECT 1", None)

    assert query_data.query_scalar(cur, "SELECT 2", ("x",)) is None
    assert calls[1] == ("SELECT 2", ("x",))

    assert query_data.query_scalar(cur, "SELECT 3") is None
    assert calls[2] == ("SELECT 3", None)
