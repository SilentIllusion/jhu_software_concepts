import pytest


@pytest.mark.buttons
def test_post_pull_data_returns_200_and_triggers_loader(run_module, monkeypatch, sample_entries):
    run, app, _ = run_module
    client = app.test_client()

    called = {"scrape": 0, "clean": 0}

    def fake_scrape(existing_urls, latest_date=None):
        called["scrape"] += 1
        return sample_entries

    def fake_clean(entries):
        called["clean"] += 1
        return entries

    monkeypatch.setattr(run, "scrape_new_data", fake_scrape)
    monkeypatch.setattr(run, "clean_data", fake_clean)

    response = client.post("/pull-data", follow_redirects=True)

    assert response.status_code == 200
    assert called["scrape"] == 1
    assert called["clean"] == 1


@pytest.mark.buttons
def test_post_update_analysis_returns_200_when_not_busy(run_module):
    _, app, _ = run_module
    client = app.test_client()

    response = client.post("/update-analysis", follow_redirects=True)

    assert response.status_code == 200


@pytest.mark.buttons
def test_busy_gating_returns_409_and_no_update(run_module):
    run, app, _ = run_module
    client = app.test_client()

    run.scrape_state["running"] = True
    response_update = client.post("/update-analysis")
    response_pull = client.post("/pull-data")

    assert response_update.status_code == 409
    assert response_pull.status_code == 409
