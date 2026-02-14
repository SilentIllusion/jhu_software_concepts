"""Tests for scraper helpers and network/persistence flows."""

import json
from datetime import date, datetime
from pathlib import Path
import types

import pytest

import scripts.scrape as scrape


class Resp:
    def __init__(self, status, html):
        self.status = status
        self.data = html.encode("utf-8")


class FakeHTTP:
    def __init__(self, responses):
        self.responses = list(responses)
        self.i = 0

    def request(self, method, url):
        item = self.responses[self.i]
        self.i += 1
        if isinstance(item, Exception):
            raise item
        return item


def make_html():
    """Build minimal HTML snippet representing one result row."""
    return """
    <table><tbody class='tw-divide-y'>
      <tr>
        <td><div class='tw-font-medium'>U</div></td>
        <td><div class='tw-text-gray-900'><span>P</span><span>PhD</span></div></td>
        <td>February 01, 2026</td>
        <td><div class='tw-inline-flex'>Accepted on 1 Jan</div><a href='/result/1'></a></td>
      </tr>
      <tr class='tw-border-none'>
        <td colspan='4'>
          <div class='tw-inline-flex'>Fall 2026</div>
          <div class='tw-inline-flex'>International</div>
          <div class='tw-inline-flex'>GPA 3.90</div>
          <div class='tw-inline-flex'>GRE 330</div>
          <div class='tw-inline-flex'>GRE V 166</div>
          <div class='tw-inline-flex'>GRE AW 4.5</div>
        </td>
      </tr>
      <tr class='tw-border-none'><td colspan='4'><p>Comment GPA 3.80</p></td></tr>
    </tbody></table>
    """


@pytest.mark.analysis
def test_helper_parsers():
    """Happy-path parsing of headers, GRE fields, GPA, decision, semester, type, degree."""
    assert "User-Agent" in scrape._build_request_headers()
    assert scrape._extract_gre_from_text("GRE 320 GRE V 160 AW 4.0") == ("320", "160", "4.0")
    assert scrape._extract_gre_from_badge_text("GRE 330 Verbal 166 AW 4.5") == ("330", "166", "4.5")
    assert scrape._extract_gpa_from_text("GPA: 3.9") == 3.9
    assert scrape._parse_decision_date("Rejected on 7 Jun") == ("Rejected", "7 Jun")
    assert scrape._parse_semester("Spring 2025") == "Spring 2025"
    assert scrape._parse_student_type("American") == "American"
    assert scrape._parse_degree("MBA track") == "MBA"


@pytest.mark.analysis
def test_helper_edge_cases(monkeypatch):
    """Edge-case parsing coverage for empty/invalid inputs."""
    # missing/empty inputs
    assert scrape._extract_gre_from_text("") == (None, None, None)
    assert scrape._extract_gre_from_badge_text(None) == (None, None, None)
    assert scrape._extract_gpa_from_text(None) is None
    # force ValueError branch by monkeypatching float
    import builtins

    monkeypatch.setattr(builtins, "float", lambda x: (_ for _ in ()).throw(ValueError))
    assert scrape._extract_gpa_from_text("GPA 3.7") is None
    # restore happens via monkeypatch fixture cleanup
    assert scrape._parse_decision_date(None) == (None, None)
    assert scrape._parse_decision_date("Maybe later") == (None, None)
    assert scrape._parse_decision_date("Interview on 5 Feb") == ("Interview", "5 Feb")
    assert scrape._parse_decision_date("Waitlisted on 3 Mar") == ("Wait listed", "3 Mar")
    assert scrape._parse_semester("") is None
    assert scrape._parse_student_type(None) is None
    assert scrape._parse_student_type("Other applicant") == "Other"
    assert scrape._parse_degree(None) is None
    assert scrape._parse_degree("Unspecified cert") is None
    assert scrape._parse_added_date("bad date") is None
    assert scrape._parse_added_date(123) is None


@pytest.mark.integration
def test_scrape_data_and_new(monkeypatch):
    """scrape_data and scrape_new_data handle success, errors, and stop conditions."""
    monkeypatch.setattr(
        scrape,
        "PoolManager",
        lambda **kwargs: FakeHTTP([Resp(200, make_html()), Resp(200, "<table><tbody class='tw-divide-y'></tbody></table>")]),
    )
    rows = scrape.scrape_data(max_entries=1)
    assert len(rows) == 1

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(500, "x")]))
    assert scrape.scrape_data(max_entries=1) == []

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(200, make_html())]))
    assert scrape.scrape_new_data(existing_urls={"https://www.thegradcafe.com/result/1"}, max_entries=1) == []

    # No tbody branch
    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(200, "<html></html>")]))
    assert scrape.scrape_data(max_entries=1) == []

    # page_new == 0 branch
    html_no_new = """
    <table><tbody class='tw-divide-y'>
      <tr><td><div class='tw-font-medium'>U</div></td><td><div class='tw-text-gray-900'><span>P</span></div></td><td>Feb 02, 2026</td><td><div class='tw-inline-flex'>Accepted</div><a href='/result/2'></a></td></tr>
    </tbody></table>
    """
    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(200, html_no_new)]))
    assert scrape.scrape_new_data(existing_urls={"https://www.thegradcafe.com/result/2"}, max_entries=2) == []


@pytest.mark.analysis
def test_dates_and_save(tmp_path):
    """Date parsing utility and JSON persistence helper."""
    assert scrape._parse_added_date(None) is None
    assert scrape._parse_added_date(datetime(2026, 2, 1)) == datetime(2026, 2, 1)
    assert scrape._parse_added_date(date(2026, 2, 1)) == datetime(2026, 2, 1)
    assert scrape._parse_added_date("February 01, 2026") == datetime(2026, 2, 1)

    fp = tmp_path / "scraped.json"
    scrape.save_scraped_data([{"a": 1}], fp)
    with open(fp, "r", encoding="utf-8") as fh:
        assert json.load(fh) == [{"a": 1}]


@pytest.mark.integration
def test_import_fallback(monkeypatch):
    """Import fallback works when package import fails."""
    import importlib.util
    import sys

    monkeypatch.setitem(sys.modules, "clean", types.SimpleNamespace(clean_data=lambda x: x, save_data=lambda x: None))
    path = Path(__file__).resolve().parents[1] / "src" / "scripts" / "scrape.py"
    spec = importlib.util.spec_from_file_location("scrape_fallback", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    assert hasattr(mod, "scrape_data")
