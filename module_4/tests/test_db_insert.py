"""Database insert and analysis data contract tests."""

import pytest


@pytest.mark.db
def test_insert_on_pull_writes_rows_with_required_fields(run_module, monkeypatch, sample_entries):
    """POST /pull-data inserts rows with non-null required fields."""
    run, app, fake_conn = run_module
    client = app.test_client()

    monkeypatch.setattr(run, "scrape_new_data", lambda existing_urls, latest_date=None: sample_entries)
    monkeypatch.setattr(run, "clean_data", lambda entries: entries)

    assert len(fake_conn.rows) == 0

    response = client.post("/pull-data", follow_redirects=True)

    assert response.status_code == 200
    assert len(fake_conn.rows) == 2

    for row in fake_conn.rows:
        assert row[0] is not None  # program
        assert row[3] is not None  # url
        assert row[4] is not None  # status


@pytest.mark.db
def test_idempotent_insert_does_not_duplicate_urls(run_module, sample_entries):
    """Duplicate URLs are not inserted multiple times."""
    run, _, fake_conn = run_module

    inserted_first = run._insert_entries(fake_conn, sample_entries)
    inserted_second = run._insert_entries(fake_conn, sample_entries)

    assert inserted_first == 2
    assert inserted_second == 2  # function returns attempted inserts after in-batch dedupe
    unique_urls = {row[3] for row in fake_conn.rows}
    assert len(unique_urls) == len(fake_conn.rows) == 2


@pytest.mark.db
def test_get_analysis_data_returns_expected_keys(run_module):
    """Analysis data dict includes all expected answer keys."""
    run, _, _ = run_module

    data = run.get_analysis_data()

    expected_keys = {
        "intl_pct",
        "count_fall_2026",
        "avg_gpa",
        "avg_gre",
        "avg_gre_v",
        "avg_gre_aw",
        "avg_gpa_american_fall_2026",
        "pct_fall_2026_accept",
        "avg_gpa_fall_2026_accept",
        "jhu_ms_cs_count",
        "cs_phd_2026_top_count",
        "cs_phd_2026_top_count_llm",
        "counts_change",
        "change_explanation",
        "total_ai_count",
        "ai_avg_gpa",
        "scrape_running",
        "scrape_message",
        "scrape_last_run",
    }
    assert expected_keys.issubset(set(data.keys()))
