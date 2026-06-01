"""Tests for POST /summarize_logs endpoint."""


def test_summarize_logs_success(client, api_headers, summarize_logs_payload):
    """Test successful log summarization."""
    response = client.post("/summarize_logs", json=summarize_logs_payload, headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "severity" in data
    assert "evidence" in data


def test_summarize_logs_missing_auth(client, summarize_logs_payload):
    """Test that missing auth returns 401."""
    response = client.post("/summarize_logs", json=summarize_logs_payload)
    assert response.status_code == 401


def test_summarize_logs_empty_logs(client, api_headers):
    """Test that empty logs returns 422."""
    payload = {
        "logs": [],
        "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"},
    }
    response = client.post("/summarize_logs", json=payload, headers=api_headers)
    assert response.status_code == 422


def test_summarize_logs_single_log(client, api_headers):
    """Test with a single log entry."""
    payload = {
        "logs": [{"message": "Single error message", "level": "ERROR"}],
        "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"},
    }
    response = client.post("/summarize_logs", json=payload, headers=api_headers)
    assert response.status_code == 200
