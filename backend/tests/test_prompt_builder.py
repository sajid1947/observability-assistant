"""Tests for the prompt builder service."""

from app.services.prompt_builder import (
    get_system_prompt,
    build_analyze_prompt,
    build_summarize_logs_prompt,
    build_explain_metric_prompt,
)
from app.services.normalizer import NormalizedData


def test_system_prompt_contains_key_instructions():
    """System prompt must contain critical instructions."""
    prompt = get_system_prompt()
    assert "SRE" in prompt
    assert "observability" in prompt
    assert "JSON" in prompt
    assert "hallucination" in prompt
    assert "severity" in prompt
    assert "confidence" in prompt


def test_build_analyze_prompt():
    """Test analyze prompt includes metric data."""
    data = NormalizedData(
        data_type="metrics",
        source="grafana",
        time_range={"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"},
        metric_descriptions=["Metric 'cpu': min=10, max=95, avg=50"],
        labels={"env": "prod"},
    )
    prompt = build_analyze_prompt(data)
    assert "grafana" in prompt
    assert "cpu" in prompt
    assert "2024-01-01" in prompt


def test_build_summarize_logs_prompt():
    """Test logs prompt includes log entries."""
    data = NormalizedData(
        data_type="logs",
        source="kibana",
        time_range={"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"},
        summary_stats={"total_logs": 3, "level_distribution": {"ERROR": 2, "INFO": 1}},
        log_summaries=["[ERROR] Connection failed", "[ERROR] Timeout", "[INFO] OK"],
    )
    prompt = build_summarize_logs_prompt(data)
    assert "kibana" in prompt
    assert "ERROR" in prompt
    assert "Connection failed" in prompt


def test_build_explain_metric_prompt():
    """Test metric explanation prompt includes stats."""
    data = NormalizedData(
        data_type="metric_detail",
        source="grafana",
        time_range={"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"},
        summary_stats={
            "metric_name": "latency_p99",
            "data_points": 10,
            "min": 0.1,
            "max": 2.5,
            "avg": 0.5,
            "latest": 2.5,
            "trend": "increasing",
        },
        metric_descriptions=["Metric: latency_p99", "Trend: increasing"],
    )
    prompt = build_explain_metric_prompt(data)
    assert "latency_p99" in prompt
    assert "increasing" in prompt
