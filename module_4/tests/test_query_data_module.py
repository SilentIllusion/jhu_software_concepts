import io
import runpy
import types

import pytest


class FakeCursor:
    def __init__(self, values):
        self.values = list(values)
        self.idx = 0

    def execute(self, sql, params=None):
        return None

    def fetchone(self):
        if self.idx >= len(self.values):
            return (None,)
        v = self.values[self.idx]
        self.idx += 1
        return (v,)

    def close(self):
        return None


class FakeConn:
    def __init__(self, values):
        self.cur = FakeCursor(values)

    def cursor(self):
        return self.cur

    def close(self):
        return None


@pytest.mark.db
def test_query_data_connection_and_scalar(monkeypatch):
    import query_data

    sentinel = object()
    monkeypatch.setattr(query_data.psycopg, "connect", lambda **kwargs: sentinel)
    assert query_data.get_db_connection() is sentinel

    class C:
        def __init__(self):
            self.called = []

        def execute(self, sql, params=None):
            self.called.append((sql, params))

        def fetchone(self):
            return None

    cur = C()
    assert query_data.query_scalar(cur, "select 1") is None
    assert cur.called[0] == ("select 1", None)
    cur.fetchone = lambda: (9,)
    assert query_data.query_scalar(cur, "select 2", ("x",)) == 9
    assert cur.called[1] == ("select 2", ("x",))


@pytest.mark.db
def test_query_data_main(monkeypatch, capsys):
    fake_conn = FakeConn([10, 20.5, 3.8, 320, 160, 4.0, 3.7, 50.0, 3.9, 2, 3, 4, 5, 3.95])
    fake_psycopg = types.SimpleNamespace(connect=lambda **kwargs: fake_conn)
    monkeypatch.setitem(__import__("sys").modules, "psycopg", fake_psycopg)

    runpy.run_module("query_data", run_name="__main__")
    out = capsys.readouterr().out
    assert "How many entries do you have in your database" in out
    assert "Do the numbers for question 8 change" in out
