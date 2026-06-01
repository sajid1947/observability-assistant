"""
Pydantic request models for all API endpoints.

These models enforce strict validation on incoming payloads.
Each model corresponds to a specific API endpoint and defines
the expected shape of the request body with type constraints,
max lengths, and default values.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Any, Optional
from datetime import datetime


class TimeRange(BaseModel):
    """
    Time range specification used across all endpoints.
    Supports both ISO 8601 strings and relative expressions (e.g., "now-1h").
    """
    start: str = Field(..., max_length=64, description="Start time (ISO 8601 or relative like 'now-1h')")
    end: str = Field(..., max_length=64, description="End time (ISO 8601 or relative like 'now')")


class MetricData(BaseModel):
    """A single metric with its name, values, and associated labels."""
    name: str = Field(..., max_length=512, description="Metric name (e.g., 'cpu_usage_percent')")
    values: list[float | int | None] = Field(default_factory=list, description="Time-series values")
    timestamps: list[str] = Field(default_factory=list, description="Corresponding timestamps")
    labels: dict[str, str] = Field(default_factory=dict, description="Labels/tags (e.g., {'host': 'web-01'})")


class AnalyzeRequest(BaseModel):
    """
    Request body for POST /analyze.
    
    Accepts dashboard data from Grafana — metrics, labels, time range,
    and optional raw query results for comprehensive analysis.
    """
    source: str = Field(
        default="grafana",
        max_length=64,
        description="Data source identifier (e.g., 'grafana', 'prometheus')"
    )
    metrics: list[MetricData] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of metrics to analyze"
    )
    time_range: TimeRange = Field(..., description="Analysis time window")
    labels: dict[str, str] = Field(
        default_factory=dict,
        description="Global labels/tags for context"
    )
    query_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Raw query results from data source"
    )
    dashboard_name: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Name of the originating dashboard"
    )
    panel_name: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Name of the originating panel"
    )

    @field_validator("metrics")
    @classmethod
    def validate_metrics_not_empty(cls, v: list[MetricData]) -> list[MetricData]:
        """Ensure at least one metric has actual data."""
        if not any(m.values for m in v):
            raise ValueError("At least one metric must contain values")
        return v


class LogEntry(BaseModel):
    """A single log entry with its message, level, and metadata."""
    message: str = Field(..., max_length=10_000, description="Log message content")
    level: Optional[str] = Field(default=None, max_length=32, description="Log level (ERROR, WARN, INFO, etc.)")
    timestamp: Optional[str] = Field(default=None, max_length=64, description="Log timestamp")
    source: Optional[str] = Field(default=None, max_length=256, description="Log source (file, service, etc.)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional log metadata")


class SummarizeLogsRequest(BaseModel):
    """
    Request body for POST /summarize_logs.
    
    Accepts log entries from Kibana or any log aggregator,
    along with active filters and time range for context.
    """
    logs: list[LogEntry] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Log entries to summarize"
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Active filters (e.g., {'level': 'ERROR', 'service': 'api-gateway'})"
    )
    time_range: TimeRange = Field(..., description="Log time window")
    source: str = Field(
        default="kibana",
        max_length=64,
        description="Source system"
    )
    index_pattern: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Elasticsearch index pattern"
    )


class ExplainMetricsRequest(BaseModel):
    """
    Request body for POST /explain_metrics.
    
    Accepts a specific metric's time-series data for detailed
    explanation including anomaly detection and trend analysis.
    """
    metric_name: str = Field(..., max_length=512, description="Name of the metric to explain")
    values: list[float | int | None] = Field(
        ...,
        min_length=1,
        description="Time-series values for the metric"
    )
    timestamps: list[str] = Field(
        default_factory=list,
        description="Corresponding timestamps"
    )
    labels: dict[str, str] = Field(
        default_factory=dict,
        description="Metric labels/tags"
    )
    time_range: TimeRange = Field(..., description="Query time range")
    query: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Original query (e.g., PromQL expression)"
    )
    threshold: Optional[float] = Field(
        default=None,
        description="Alert threshold value, if any"
    )
    unit: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Metric unit (e.g., 'percent', 'bytes', 'ms')"
    )
