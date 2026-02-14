import json
import runpy

import pytest

from src.app.scripts import clean


@pytest.mark.analysis
def test_strip_and_normalize_helpers():
    assert clean._strip_html(None) is None
    assert clean._strip_html(123) is None
    assert clean._strip_html("   ") is None
    assert clean._strip_html("<b>Hello</b>") == "Hello"
    assert clean._strip_html("Plain") == "Plain"

    assert clean._normalize_value(None) is None
    assert clean._normalize_value("null") is None
    assert clean._normalize_value("none") is None
    assert clean._normalize_value(4.2) == 4.2
    assert clean._normalize_value("<i>x</i>") == "x"
    assert clean._normalize_value(object()) is None


@pytest.mark.analysis
def test_clean_single_entry_and_clean_data_paths():
    entry = {
        "program_name": "CS",
        "university": "JHU",
        "comments": "A\x00\x01   B",
        "extra": "<b>ok</b>",
        "llm-generated-program": "skip",
    }
    out = clean._clean_single_entry(entry)
    assert out["program"] == "CS, JHU"
    assert out["extra"] == "ok"
    assert "llm-generated-program" not in out
    only_program = clean._clean_single_entry({"program_name": "Only Program"})
    assert only_program["program"] == "Only Program"
    only_university = clean._clean_single_entry({"university": "Only University"})
    assert only_university["program"] == "Only University"
    assert "unused" not in clean._clean_single_entry({"unused": ""})

    cleaned_list = clean.clean_data(["not-dict", {"program": "X\x00", "comments": "Y   Z"}])
    assert len(cleaned_list) == 1
    assert cleaned_list[0]["program"] == "X"
    assert cleaned_list[0]["comments"] == "Y Z"

    assert clean._remove_messy_content(None) is None
    assert clean._remove_messy_content("\x00 A   B \x7f") == "A B"


@pytest.mark.analysis
def test_replace_none_save_load_and_main(tmp_path, monkeypatch):
    nested = {"a": None, "b": [1, None, {"c": None}]}
    assert clean._replace_none_with_string(nested) == {"a": "none", "b": [1, "none", {"c": "none"}]}

    fp = tmp_path / "data.json"
    clean.save_data([{"x": None}], str(fp))
    loaded = clean.load_data(str(fp))
    assert loaded == [{"x": "none"}]

    monkeypatch.chdir(tmp_path)
    with open("applicant_data.json", "w", encoding="utf-8") as fh:
        json.dump([{"program": "<b>CS</b>", "comments": "ok"}], fh)

    runpy.run_module("scripts.clean", run_name="__main__")
    with open("applicant_data.json", "r", encoding="utf-8") as fh:
        saved = json.load(fh)
    assert saved[0]["program"] == "CS"
