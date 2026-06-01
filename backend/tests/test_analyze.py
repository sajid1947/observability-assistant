"""Tests for POST /analyze endpoint."""


def test_analyze_success(client, api_headers, analyze_payload):
    """Test successful metric analysis returns valid InsightResponse."""
    response = client.post("/analyze", json=analyze_payload, headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "root_cause" in data
    assert "severity" in data
    assert data["severity"] in ["critical", "high", "medium", "low", "info"]
    assert "confidence" in data
    assert "evidence" in data
    assert isinstance(data["evidence"], list)
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)


def test_analyze_missing_api_key(client, analyze_payload):
    """Test that missing API key returns 401."""
    response = client.post("/analyze", json=analyze_payload)
    assert response.status_code == 401


def test_analyze_invalid_api_key(client, analyze_payload):
    """Test that invalid API key returns 403."""
    headers = {"X-API-Key": "wrong-key", "Content-Type": "application/json"}
    response = client.post("/analyze", json=analyze_payload, headers=headers)
    assert response.status_code == 403


def test_analyze_empty_metrics(client, api_headers):
    """Test that empty metrics list returns 422."""
    payload = {
        "source": "grafana",
        "metrics": [],
        "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"},
    }
    response = client.post("/analyze", json=payload, headers=api_headers)
    assert response.status_code == 422


def test_analyze_has_request_id(client, api_headers, analyze_payload):
    """Test that response includes X-Request-ID header."""
    response = client.post("/analyze", json=analyze_payload, headers=api_headers)
    assert "X-Request-ID" in response.headers


def test_analyze_caching(client, api_headers, analyze_payload):
    """Test that identical requests return cached responses."""
    # First request
    r1 = client.post("/analyze", json=analyze_payload, headers=api_headers)
    assert r1.status_code == 200

    # Second identical request should be cached
    r2 = client.post("/analyze", json=analyze_payload, headers=api_headers)
    assert r2.status_code == 200
    assert r2.json()["cached"] is True
