"""Shared fixtures and fakes for the Grad Cafe test suite."""

import sys
import types
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[1] / "src" / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.last_sql = ""

    def execute(self, sql, params=None):
        self.last_sql = sql
        self.conn.executed.append((sql, params))

    def fetchone(self):
        sql = self.last_sql
        if "ORDER BY date_added DESC" in sql:
            dates = [row[2] for row in self.conn.rows if len(row) > 2 and row[2]]
            return (max(dates),) if dates else (None,)

        if self.conn.metric_index < len(self.conn.metrics):
            value = self.conn.metrics[self.conn.metric_index]
            self.conn.metric_index += 1
            return (value,)
        return (None,)

    def fetchall(self):
        if "SELECT url FROM admission_results" in self.last_sql:
            return [(row[3],) for row in self.conn.rows if len(row) > 3 and row[3]]
        return []

    def executemany(self, sql, data):
        self.conn.executemany_calls.append((sql, data))
        for row in data:
            if any(existing[3] == row[3] for existing in self.conn.rows):
                continue
            self.conn.rows.append(row)

    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, metrics=None):
        self.metrics = list(
            metrics
            if metrics is not None
            else [12.3, 5, 3.8, 320.0, 160.0, 4.0, 3.7, 55.5, 3.9, 1, 2, 3, 4, 3.95]
        )
        self.metric_index = 0
        self.rows = []
        self.closed = False
        self.executed = []
        self.executemany_calls = []
        self.commits = 0

    def cursor(self):
        self.metric_index = 0
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


@pytest.fixture
def sample_entries():
    return [
        {
            "program": "Computer Science, Johns Hopkins University",
            "comments": "GRE 330 GPA 3.9",
            "date_added": "February 01, 2026",
            "url": "https://www.thegradcafe.com/result/10001",
            "applicant_status": "Accepted",
            "semester_year": "Fall 2026",
            "international_american": "American",
            "gre_score": 330.0,
            "gre_v_score": 166.0,
            "degree_type": "PhD",
            "gpa": 3.9,
            "gre_aw": 4.5,
        },
        {
            "program": "Artificial Intelligence, Carnegie Mellon University",
            "comments": "test",
            "date_added": "February 02, 2026",
            "url": "https://www.thegradcafe.com/result/10002",
            "applicant_status": "Accepted",
            "semester_year": "Fall 2026",
            "international_american": "International",
            "gre_score": 325.0,
            "gre_v_score": 164.0,
            "degree_type": "Masters",
            "gpa": 3.8,
            "gre_aw": 4.0,
        },
    ]


@pytest.fixture
def run_module(monkeypatch):
    fake_conn = FakeConnection()
    fake_psycopg = types.SimpleNamespace(connect=lambda **kwargs: fake_conn)
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)

    import run

    run.scrape_state["running"] = False
    run.scrape_state["message"] = None
    run.scrape_state["last_run"] = None

    monkeypatch.setattr(run, "get_db_connection", lambda: fake_conn)

    app = run.create_app({"TESTING": True, "SYNC_PULL_DATA": True})
    return run, app, fake_conn
