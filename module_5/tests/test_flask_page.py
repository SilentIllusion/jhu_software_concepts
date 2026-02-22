"""Tests for Flask page rendering and blueprint registration."""

import pytest


@pytest.mark.web
def test_create_app_and_blueprint(run_module):
    """App factory registers the pages blueprint."""
    _, app, _ = run_module
    assert app is not None
    assert app.blueprints.get("pages") is not None


@pytest.mark.web
def test_analysis_page_renders_required_content(run_module):
    """GET /analysis returns the dashboard with required buttons and labels."""
    _, app, _ = run_module
    client = app.test_client()

    response = client.get("/analysis")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Analysis" in html
    assert "Pull Data" in html
    assert "Update Analysis" in html
    assert "Answer:" in html


@pytest.mark.web
def test_root_redirects_to_analysis(run_module):
    """Root path redirects to /analysis."""
    _, app, _ = run_module
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 302
    assert "/analysis" in response.headers["Location"]

