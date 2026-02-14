import json
import runpy
import sys
from datetime import date, datetime
from pathlib import Path
import importlib.util
import types

from bs4 import BeautifulSoup
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


def make_html(with_url=True):
    link = '<a href="/result/123"></a>' if with_url else ""
    return f"""
    <table><tbody class='tw-divide-y'>
      <tr>
        <td><div class='tw-font-medium'>JHU</div></td>
        <td><div class='tw-text-gray-900'><span>Computer Science</span><span>PhD</span></div></td>
        <td>February 01, 2026</td>
        <td><div class='tw-inline-flex'>Accepted on 29 Jan</div>{link}</td>
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
def test_scrape_helper_parsers_and_listing_row(monkeypatch):
    assert "User-Agent" in scrape._build_request_headers()
    assert scrape._extract_gre_from_text("") == (None, None, None)
    assert scrape._extract_gre_from_badge_text("") == (None, None, None)
    assert scrape._extract_gre_from_text("GRE 320 GRE V 160 AW 4.0") == ("320", "160", "4.0")
    assert scrape._extract_gre_from_badge_text("GRE 330 Verbal 166 AW 4.5") == ("330", "166", "4.5")

    monkeypatch.setattr(scrape.re, "search", lambda *args, **kwargs: None)
    assert scrape._extract_gpa_from_text("") is None
    assert scrape._extract_gpa_from_text("GPA 3.9") is None
    monkeypatch.undo()

    assert scrape._extract_gpa_from_text("GPA: 3.9") == 3.9
    assert scrape._parse_decision_date("") == (None, None)
    assert scrape._parse_decision_date("Rejected on 7 Jun") == ("Rejected", "7 Jun")
    assert scrape._parse_decision_date("Interview") == ("Interview", None)
    assert scrape._parse_decision_date("Waitlisted") == ("Wait listed", None)
    assert scrape._parse_decision_date("Other") == (None, None)
    assert scrape._parse_semester("Spring 2025") == "Spring 2025"
    assert scrape._parse_semester("") is None
    assert scrape._parse_semester("bad") is None
    assert scrape._parse_student_type("") is None
    assert scrape._parse_student_type("American") == "American"
    assert scrape._parse_student_type("Other") == "Other"
    assert scrape._parse_student_type("blah") is None
    assert scrape._parse_degree("MBA track") == "MBA"
    assert scrape._parse_degree("unknown degree") is None
    assert scrape._parse_degree("") is None

    soup = BeautifulSoup(make_html(with_url=True), "html.parser")
    rows = soup.find_all("tr")
    entry = scrape._parse_listing_row(rows[0], rows[1], rows[2])
    assert entry["program"] == "Computer Science, JHU"
    assert entry["acceptance_date"] == "29 Jan"
    assert entry["url"].endswith("/result/123")

    bad = BeautifulSoup("<tr><td>x</td></tr>", "html.parser").find("tr")
    assert scrape._parse_listing_row(bad, None, None) is None

    # Rejected path and default GRE values path.
    rejected_soup = BeautifulSoup(
        """
        <table><tbody class='tw-divide-y'>
          <tr>
            <td><div class='tw-font-medium'></div></td>
            <td><div class='tw-text-gray-900'><span>ProgramOnly</span></div></td>
            <td>February 01, 2026</td>
            <td><div class='tw-inline-flex'>Rejected on 1 Jan</div><a href='/result/999'></a></td>
          </tr>
          <tr class='tw-border-none'><td colspan='4'><div class='tw-inline-flex'></div></td></tr>
          <tr class='tw-border-none'><td colspan='4'><p>GPA 3.50</p></td></tr>
        </tbody></table>
        """,
        "html.parser",
    )
    rrows = rejected_soup.find_all("tr")
    rejected = scrape._parse_listing_row(rrows[0], rrows[1], rrows[2])
    assert rejected["program"] == "ProgramOnly"
    assert rejected["rejection_date"] == "1 Jan"
    assert rejected["gpa"] == 3.5
    assert rejected["gre_score"] == 0.0
    assert rejected["gre_v_score"] == 0.0
    assert rejected["gre_aw"] == 0.0

    # University-only path.
    uni_soup = BeautifulSoup(
        """
        <tr>
          <td><div class='tw-font-medium'>OnlyU</div></td>
          <td><div class='tw-text-gray-900'></div></td>
          <td>February 01, 2026</td>
          <td><div class='tw-inline-flex'>Accepted on 2 Jan</div></td>
        </tr>
        """,
        "html.parser",
    )
    uni_entry = scrape._parse_listing_row(uni_soup.find("tr"), None, None)
    assert uni_entry["program"] == "OnlyU"


@pytest.mark.integration
def test_scrape_data_and_new_data_flows(monkeypatch):
    saved = {"rows": None}
    monkeypatch.setattr(scrape, "save_data", lambda rows: saved.__setitem__("rows", rows))

    monkeypatch.setattr(
        scrape,
        "PoolManager",
        lambda **kwargs: FakeHTTP([
            Resp(200, make_html(True)),
            Resp(200, "<table><tbody class='tw-divide-y'></tbody></table>"),
        ]),
    )
    rows = scrape.scrape_data(max_entries=5)
    assert len(rows) == 1
    assert saved["rows"] is not None

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(500, "x")]))
    assert scrape.scrape_data(max_entries=1) == []

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Exception("boom")]))
    assert scrape.scrape_data(max_entries=1) == []

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(200, "<html></html>")]))
    assert scrape.scrape_new_data(existing_urls=set(), max_entries=1) == []

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(200, "<html></html>")]))
    assert scrape.scrape_data(max_entries=1) == []

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(200, make_html(True))]))
    out = scrape.scrape_new_data(existing_urls={"https://www.thegradcafe.com/result/123"}, max_entries=2)
    assert out == []

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(200, make_html(True))]))
    out2 = scrape.scrape_new_data(existing_urls=set(), max_entries=2, latest_date="February 01, 2026")
    assert out2 == []

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(200, make_html(True))]))
    out3 = scrape.scrape_new_data(existing_urls=set(), max_entries=1)
    assert len(out3) == 1

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(500, "x")]))
    assert scrape.scrape_new_data(existing_urls=set(), max_entries=1) == []

    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Exception("new boom")]))
    assert scrape.scrape_new_data(existing_urls=set(), max_entries=1) == []

    # Border-none row first triggers skip branch.
    border_html = """
    <table><tbody class='tw-divide-y'>
      <tr class='tw-border-none'><td>skip</td></tr>
      <tr><td><div class='tw-font-medium'>U</div></td><td><div class='tw-text-gray-900'><span>P</span></div></td><td>February 02, 2026</td><td><div class='tw-inline-flex'>Accepted on 2 Jan</div><a href='/result/124'></a></td></tr>
    </tbody></table>
    """
    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(200, border_html), Resp(200, "<table><tbody class='tw-divide-y'></tbody></table>")]))
    assert len(scrape.scrape_data(max_entries=1)) == 1

    # new-data page increment and second-page URL branch.
    monkeypatch.setattr(scrape, "PoolManager", lambda **kwargs: FakeHTTP([Resp(200, border_html), Resp(200, "<table><tbody class='tw-divide-y'></tbody></table>")]))
    assert len(scrape.scrape_new_data(existing_urls=set(), max_entries=5, max_pages=2)) == 1


@pytest.mark.analysis
def test_parse_added_date_and_save_file(tmp_path):
    assert scrape._parse_added_date(None) is None
    dt = datetime(2026, 2, 1)
    assert scrape._parse_added_date(dt) == dt
    assert scrape._parse_added_date(date(2026, 2, 1)) == datetime(2026, 2, 1)
    assert scrape._parse_added_date(123) is None
    assert scrape._parse_added_date("February 01, 2026") == datetime(2026, 2, 1)
    assert scrape._parse_added_date("Feb 01, 2026") == datetime(2026, 2, 1)
    assert scrape._parse_added_date("February 01 2026") == datetime(2026, 2, 1)
    assert scrape._parse_added_date("Feb 01 2026") == datetime(2026, 2, 1)
    assert scrape._parse_added_date("not-a-date") is None

    fp = tmp_path / "scraped.json"
    scrape.save_scraped_data([{"a": 1}], str(fp))
    with open(fp, "r", encoding="utf-8") as fh:
        assert json.load(fh) == [{"a": 1}]


@pytest.mark.analysis
def test_extract_gpa_value_error_path(monkeypatch):
    class M:
        def group(self, _):
            return "bad-number"

    monkeypatch.setattr(scrape.re, "search", lambda *args, **kwargs: M())
    assert scrape._extract_gpa_from_text("GPA text") is None


@pytest.mark.integration
def test_scrape_module_main_and_import_fallback(monkeypatch):
    import urllib3
    import scripts.clean as clean_mod

    monkeypatch.setattr(urllib3, "PoolManager", lambda *args, **kwargs: FakeHTTP([Resp(500, "x")]))
    monkeypatch.setattr(clean_mod, "save_data", lambda entries: None)

    runpy.run_module("scripts.scrape", run_name="__main__")

    fake_clean = types.SimpleNamespace(clean_data=lambda x: x, save_data=lambda x: None)
    monkeypatch.setitem(sys.modules, "clean", fake_clean)

    path = Path(__file__).resolve().parents[1] / "src" / "app" / "scripts" / "scrape.py"
    spec = importlib.util.spec_from_file_location("scrape_fallback", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    assert hasattr(mod, "scrape_data")
