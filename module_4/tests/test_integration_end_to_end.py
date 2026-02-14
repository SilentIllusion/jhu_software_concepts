"""End-to-end flows covering pull, update, and render behaviors."""

import pytest


@pytest.mark.integration
def test_end_to_end_pull_update_render(run_module, monkeypatch, sample_entries):
    """Pull data, update analysis, and render page with expected values."""
    run, app, fake_conn = run_module
    client = app.test_client()

    monkeypatch.setattr(run, "scrape_new_data", lambda existing_urls, latest_date=None: sample_entries)
    monkeypatch.setattr(run, "clean_data", lambda entries: entries)

    pull_response = client.post("/pull-data", follow_redirects=True)
    assert pull_response.status_code == 200
    assert len(fake_conn.rows) == 2

    update_response = client.post("/update-analysis", follow_redirects=True)
    assert update_response.status_code == 200

    analysis_response = client.get("/analysis")
    assert analysis_response.status_code == 200
    html = analysis_response.get_data(as_text=True)
    assert "Answer:" in html
    assert "12.30" in html


@pytest.mark.integration
def test_multiple_pulls_with_overlap_keep_unique_rows(run_module, monkeypatch, sample_entries):
    """Repeated pulls keep URLs unique even with overlapping batches."""
    run, app, fake_conn = run_module
    client = app.test_client()

    first_batch = list(sample_entries)
    second_batch = list(sample_entries) + [
        {
            "program": "Computer Science, MIT",
            "comments": "new row",
            "date_added": "February 03, 2026",
            "url": "https://www.thegradcafe.com/result/10003",
            "applicant_status": "Accepted",
            "semester_year": "Fall 2026",
            "international_american": "International",
            "gre_score": 332.0,
            "gre_v_score": 167.0,
            "degree_type": "PhD",
            "gpa": 3.95,
            "gre_aw": 5.0,
        }
    ]

    batches = [first_batch, second_batch]

    def fake_scrape(existing_urls, latest_date=None):
        return batches.pop(0)

    monkeypatch.setattr(run, "scrape_new_data", fake_scrape)
    monkeypatch.setattr(run, "clean_data", lambda entries: entries)

    client.post("/pull-data", follow_redirects=True)
    client.post("/pull-data", follow_redirects=True)

    urls = [row[3] for row in fake_conn.rows]
    assert len(urls) == len(set(urls)) == 3
