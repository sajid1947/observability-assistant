"""Tests for GET /health endpoint."""


def test_health_check(client):
    """Test health endpoint returns valid response (no auth required)."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "uptime_seconds" in data
    assert "llm_backend" in data
    assert "llm_status" in data


def test_health_includes_cache_stats(client):
    """Test that health response includes cache statistics."""
    response = client.get("/health")
    data = response.json()
    assert "cache_stats" in data
    if data["cache_stats"]:
        assert "hits" in data["cache_stats"]
        assert "misses" in data["cache_stats"]
