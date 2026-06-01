"""Tests for POST /explain_metrics endpoint."""


def test_explain_metrics_success(client, api_headers, explain_metrics_payload):
    """Test successful metric explanation."""
    response = client.post("/explain_metrics", json=explain_metrics_payload, headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "severity" in data
    assert "recommendations" in data


def test_explain_metrics_missing_values(client, api_headers):
    """Test that empty values returns 422."""
    payload = {
        "metric_name": "test_metric",
        "values": [],
        "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"},
    }
    response = client.post("/explain_metrics", json=payload, headers=api_headers)
    assert response.status_code == 422


def test_explain_metrics_with_threshold(client, api_headers, explain_metrics_payload):
    """Test metric explanation with threshold analysis."""
    response = client.post("/explain_metrics", json=explain_metrics_payload, headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["model_used"] == "mock-model"
