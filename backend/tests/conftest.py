"""
Shared test fixtures for the backend test suite.

Provides:
- FastAPI test client (with mocked LLM client)
- Mock LLM client that returns predictable responses
- Sample payloads for each endpoint
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.clients.base import ModelClient


# ── Mock LLM Client ──

class MockModelClient(ModelClient):
    """
    Mock model client that returns a predictable JSON response.
    Used in tests to avoid hitting a real LLM backend.
    """

    @property
    def model_name(self) -> str:
        return "mock-model"

    async def _do_generate(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        return '''{
            "summary": "Test analysis complete",
            "root_cause": "Mock root cause for testing",
            "severity": "medium",
            "confidence": "75%",
            "evidence": ["Evidence point 1", "Evidence point 2"],
            "recommendations": ["Recommendation 1", "Recommendation 2"],
            "anomalies_detected": ["Test anomaly detected"]
        }'''

    async def _do_health_check(self) -> bool:
        return True


@pytest.fixture
def mock_llm_client():
    """Provide a mock LLM client and patch it into dependencies."""
    client = MockModelClient()
    with patch("app.dependencies._llm_client", client):
        with patch("app.dependencies.get_llm_client", return_value=client):
            yield client


@pytest.fixture
def client(mock_llm_client):
    """Provide a FastAPI test client with mocked LLM."""
    return TestClient(app)


@pytest.fixture
def api_headers():
    """Standard headers including API key."""
    return {
        "X-API-Key": "dev-key-change-me-in-production",
        "Content-Type": "application/json",
    }


# ── Sample Payloads ──

@pytest.fixture
def analyze_payload():
    return {
        "source": "grafana",
        "metrics": [
            {
                "name": "cpu_usage_percent",
                "values": [45.2, 48.1, 52.3, 78.9, 95.1, 92.3],
                "timestamps": [
                    "2024-01-01T00:00:00Z", "2024-01-01T00:05:00Z",
                    "2024-01-01T00:10:00Z", "2024-01-01T00:15:00Z",
                    "2024-01-01T00:20:00Z", "2024-01-01T00:25:00Z",
                ],
                "labels": {"host": "web-01", "region": "us-east-1"},
            }
        ],
        "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T00:30:00Z"},
        "labels": {"env": "production"},
        "dashboard_name": "Web Server Monitoring",
    }


@pytest.fixture
def summarize_logs_payload():
    return {
        "logs": [
            {"message": "Connection timeout to database", "level": "ERROR", "timestamp": "2024-01-01T00:15:00Z"},
            {"message": "Retrying connection attempt 3/5", "level": "WARN", "timestamp": "2024-01-01T00:15:01Z"},
            {"message": "Request processed successfully", "level": "INFO", "timestamp": "2024-01-01T00:15:02Z"},
            {"message": "Connection pool exhausted", "level": "ERROR", "timestamp": "2024-01-01T00:15:03Z"},
        ],
        "filters": {"level": "ERROR"},
        "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T00:30:00Z"},
        "source": "kibana",
    }


@pytest.fixture
def explain_metrics_payload():
    return {
        "metric_name": "http_request_duration_seconds",
        "values": [0.12, 0.15, 0.11, 0.13, 0.45, 1.2, 2.3, 0.14, 0.13],
        "timestamps": [
            "2024-01-01T00:00:00Z", "2024-01-01T00:05:00Z",
            "2024-01-01T00:10:00Z", "2024-01-01T00:15:00Z",
            "2024-01-01T00:20:00Z", "2024-01-01T00:25:00Z",
            "2024-01-01T00:30:00Z", "2024-01-01T00:35:00Z",
            "2024-01-01T00:40:00Z",
        ],
        "labels": {"service": "api-gateway", "endpoint": "/api/v1/users"},
        "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T00:45:00Z"},
        "query": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
        "threshold": 1.0,
        "unit": "seconds",
    }
