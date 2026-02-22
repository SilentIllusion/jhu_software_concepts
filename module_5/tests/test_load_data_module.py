"""Tests for the load_data helper that bulk-loads corrected JSON."""

import json
from pathlib import Path

import pytest

import load_data


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.calls = []

    def executemany(self, sql, data):
        self.calls.append((sql, data))
        self.conn.rows.extend(data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self):
        self.rows = []
        self.commits = 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


@pytest.mark.db
def test_load_corrected_data_inserts_all_rows(tmp_path):
    """load_corrected_data inserts rows using provided connection."""
    payload = [
        {
            "program": "CS, Test U",
            "comments": "hi",
            "date_added": "Feb 1, 2026",
            "url": "u1",
            "applicant_status": "Accepted",
            "semester_year": "Fall 2026",
            "international_american": "American",
            "degree_type": "PhD",
            "gre_score": 320.0,
            "gre_v_score": 160.0,
            "gpa": 3.9,
            "gre_aw": 4.5,
            "llm-generated-program": "CS",
            "llm-generated-university": "Test U",
        },
        {
            "program": "Math, Test U",
            "comments": "yo",
            "date_added": "Feb 2, 2026",
            "url": "u2",
            "applicant_status": "Accepted",
            "semester_year": "Fall 2026",
            "international_american": "International",
            "degree_type": "PhD",
            "gre_score": 330.0,
            "gre_v_score": 165.0,
            "gpa": 3.8,
            "gre_aw": 4.0,
            "llm-generated-program": "Math",
            "llm-generated-university": "Test U",
        },
    ]
    fp = Path(tmp_path) / "data.json"
    fp.write_text(json.dumps(payload), encoding="utf-8")

    conn = FakeConn()
    inserted = load_data.load_corrected_data(fp, conn=conn)

    assert inserted == 2
    assert conn.commits == 1
    assert len(conn.rows) == 2


@pytest.mark.db
def test_load_corrected_data_uses_default_connection(tmp_path, monkeypatch):
    """When no connection is provided, the helper opens and closes one."""
    payload = [
        {
            "program": "Physics, Test U",
            "comments": "ok",
            "date_added": "Feb 3, 2026",
            "url": "u3",
            "applicant_status": "Accepted",
            "semester_year": "Fall 2026",
            "international_american": "Other",
            "degree_type": "PhD",
            "gre_score": 310.0,
            "gre_v_score": 155.0,
            "gpa": 3.5,
            "gre_aw": 4.0,
            "llm-generated-program": "Physics",
            "llm-generated-university": "Test U",
        }
    ]
    fp = Path(tmp_path) / "data2.json"
    fp.write_text(json.dumps(payload), encoding="utf-8")

    class CloseConn(FakeConn):
        def __init__(self):
            super().__init__()
            self.closed = False

        def close(self):
            self.closed = True

    conn = CloseConn()
    monkeypatch.setattr(load_data, "_get_connection", lambda: conn)

    inserted = load_data.load_corrected_data(fp)

    assert inserted == 1
    assert conn.commits == 1
    assert conn.closed is True
