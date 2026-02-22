"""Unit tests for the cleaning helpers in scripts.clean."""

import json

import pytest

import scripts.clean as clean


@pytest.mark.analysis
def test_strip_and_normalize():
    """HTML stripping and normalization edge cases."""
    assert clean._strip_html(None) is None
    assert clean._strip_html(5) is None
    assert clean._strip_html("   ") is None
    assert clean._strip_html(" <b>x</b> ") == "x"
    assert clean._normalize_value("none") is None
    assert clean._normalize_value(2.5) == 2.5
    assert clean._normalize_value("<i>y</i>") == "y"


@pytest.mark.analysis
def test_clean_single_entry_and_extra_keys():
    """Cleaning a single entry preserves extras and builds program."""
    entry = {
        "program_name": "CS",
        "university": "JHU",
        "comments": "A\x00B",
        "extra": " <u>ok</u> ",
        "llm-generated-program": "skip",
    }
    cleaned = clean._clean_single_entry(entry)
    assert cleaned["program"] == "CS, JHU"
    assert cleaned["extra"] == "ok"
    assert "llm-generated-program" not in cleaned


@pytest.mark.analysis
def test_clean_data_and_messy_content():
    """Clean list input and remove messy control characters."""
    rows = clean.clean_data(["bad", {"program": "X\x00", "comments": "Y   Z", "date_added": None}])
    assert len(rows) == 1
    assert rows[0]["program"] == "X"
    assert rows[0]["comments"] == "Y Z"
    assert clean._remove_messy_content("\x00 a  b \x7f") == "a b"


@pytest.mark.analysis
def test_replace_none_save_load(tmp_path):
    """Persist cleaned data and replace None with literal string."""
    fp = tmp_path / "data.json"
    clean.save_data([{"a": None, "b": [1, None]}], fp)
    loaded = clean.load_data(fp)
    assert loaded == [{"a": "none", "b": [1, "none"]}]


@pytest.mark.analysis
def test_clean_additional_branches():
    """Cover additional normalization branches and early returns."""
    # _normalize_value fallback path
    assert clean._normalize_value({"bad": "type"}) is None

    # Backfill program when only university is provided
    only_uni = clean._clean_single_entry({"university": "Solo U"})
    assert only_uni["program"] == "Solo U"

    # Backfill program when only program_name is provided
    only_prog = clean._clean_single_entry({"program_name": "Solo Program"})
    assert only_prog["program"] == "Solo Program"

    # Extra field that is empty should be skipped
    cleaned = clean._clean_single_entry({"program": "X", "ignore_me": ""})
    assert "ignore_me" not in cleaned

    # _remove_messy_content early return on invalid input
    assert clean._remove_messy_content(None) is None
