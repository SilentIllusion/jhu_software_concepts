import re

import pytest


@pytest.mark.analysis
def test_answer_labels_rendered(run_module):
    _, app, _ = run_module
    client = app.test_client()

    response = client.get("/analysis")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert html.count("Answer:") >= 1


@pytest.mark.analysis
def test_percentage_values_have_two_decimals(run_module):
    _, app, _ = run_module
    client = app.test_client()

    response = client.get("/analysis")
    html = response.get_data(as_text=True)

    assert "12.30" in html
    assert "55.50" in html
    assert re.search(r"\b\d+\.\d{2}\b", html)
