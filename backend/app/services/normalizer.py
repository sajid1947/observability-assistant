"""
Payload normalizer service.

Converts Grafana and Kibana payloads into a uniform internal format
for prompt construction. This decouples the prompt builder from the
specific data source format, making it easy to add new integrations.
"""

from typing import Any

from app.models.requests import (
    AnalyzeRequest,
    SummarizeLogsRequest,
    ExplainMetricsRequest,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NormalizedData:
    """
    Uniform internal representation of observability data.
    
    All data sources (Grafana, Kibana, etc.) are normalized into this
    format before being passed to the prompt builder. This ensures
    consistent prompt construction regardless of the source.
    """

    def __init__(
        self,
        data_type: str,
        source: str,
        time_range: dict[str, str],
        summary_stats: dict[str, Any] | None = None,
        metric_descriptions: list[str] | None = None,
        log_summaries: list[str] | None = None,
        labels: dict[str, str] | None = None,
        raw_context: str | None = None,
    ):
        self.data_type = data_type  # "metrics", "logs", "metric_detail"
        self.source = source
        self.time_range = time_range
        self.summary_stats = summary_stats or {}
        self.metric_descriptions = metric_descriptions or []
        self.log_summaries = log_summaries or []
        self.labels = labels or {}
        self.raw_context = raw_context or ""


def normalize_analyze_request(request: AnalyzeRequest) -> NormalizedData:
    """
    Normalize a Grafana analyze request into internal format.
    
    Extracts metric names, computes basic statistics (min, max, avg, latest),
    and formats labels for inclusion in the prompt context.
    
    Args:
        request: Validated AnalyzeRequest from the API endpoint.
    
    Returns:
        NormalizedData with metric descriptions and summary stats.
    """
    metric_descriptions = []
    summary_stats: dict[str, Any] = {
        "total_metrics": len(request.metrics),
        "metrics_summary": [],
    }

    for metric in request.metrics:
        # Compute basic stats for each metric
        values = [v for v in metric.values if v is not None]
        if values:
            stats = {
                "name": metric.name,
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "avg": round(sum(values) / len(values), 4),
                "latest": values[-1] if values else None,
                "data_points": len(values),
                "labels": metric.labels,
            }
            summary_stats["metrics_summary"].append(stats)

            # Create human-readable metric description
            label_str = ", ".join(f"{k}={v}" for k, v in metric.labels.items()) if metric.labels else "no labels"
            description = (
                f"Metric '{metric.name}' ({label_str}): "
                f"min={stats['min']}, max={stats['max']}, avg={stats['avg']}, "
                f"latest={stats['latest']}, points={stats['data_points']}"
            )
            metric_descriptions.append(description)
        else:
            metric_descriptions.append(f"Metric '{metric.name}': no data points")

    context_parts = []
    if request.dashboard_name:
        context_parts.append(f"Dashboard: {request.dashboard_name}")
    if request.panel_name:
        context_parts.append(f"Panel: {request.panel_name}")
    if request.labels:
        context_parts.append(f"Global labels: {request.labels}")

    logger.info(
        "Normalized analyze request",
        source=request.source,
        metric_count=len(request.metrics),
    )

    return NormalizedData(
        data_type="metrics",
        source=request.source,
        time_range={"start": request.time_range.start, "end": request.time_range.end},
        summary_stats=summary_stats,
        metric_descriptions=metric_descriptions,
        labels=request.labels,
        raw_context="\n".join(context_parts),
    )


def normalize_logs_request(request: SummarizeLogsRequest) -> NormalizedData:
    """
    Normalize a Kibana log summarization request.
    
    Groups logs by level, computes distributions, and creates
    concise summaries suitable for LLM prompt inclusion.
    
    Args:
        request: Validated SummarizeLogsRequest from the API endpoint.
    
    Returns:
        NormalizedData with log summaries and level distribution.
    """
    # Group logs by level
    level_counts: dict[str, int] = {}
    log_summaries: list[str] = []

    for entry in request.logs:
        level = (entry.level or "UNKNOWN").upper()
        level_counts[level] = level_counts.get(level, 0) + 1

        # Create summary line for each log entry
        parts = []
        if entry.timestamp:
            parts.append(f"[{entry.timestamp}]")
        parts.append(f"[{level}]")
        if entry.source:
            parts.append(f"[{entry.source}]")
        parts.append(entry.message[:500])  # Truncate long messages
        log_summaries.append(" ".join(parts))

    summary_stats: dict[str, Any] = {
        "total_logs": len(request.logs),
        "level_distribution": level_counts,
        "filters_applied": request.filters,
    }

    context_parts = []
    if request.index_pattern:
        context_parts.append(f"Index pattern: {request.index_pattern}")
    if request.filters:
        context_parts.append(f"Active filters: {request.filters}")

    logger.info(
        "Normalized logs request",
        source=request.source,
        log_count=len(request.logs),
        level_distribution=level_counts,
    )

    return NormalizedData(
        data_type="logs",
        source=request.source,
        time_range={"start": request.time_range.start, "end": request.time_range.end},
        summary_stats=summary_stats,
        log_summaries=log_summaries,
        raw_context="\n".join(context_parts),
    )


def normalize_explain_metrics_request(request: ExplainMetricsRequest) -> NormalizedData:
    """
    Normalize a metric explanation request.
    
    Provides detailed statistics for a single metric including
    trend detection (increasing/decreasing/stable) and threshold
    proximity analysis.
    
    Args:
        request: Validated ExplainMetricsRequest from the API endpoint.
    
    Returns:
        NormalizedData with detailed metric analysis.
    """
    values = [v for v in request.values if v is not None]
    stats: dict[str, Any] = {
        "metric_name": request.metric_name,
        "data_points": len(values),
    }

    if values:
        stats.update({
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "avg": round(sum(values) / len(values), 4),
            "latest": values[-1],
            "first": values[0],
        })

        # Simple trend detection
        if len(values) >= 2:
            first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
            second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            if second_half_avg > first_half_avg * 1.1:
                stats["trend"] = "increasing"
            elif second_half_avg < first_half_avg * 0.9:
                stats["trend"] = "decreasing"
            else:
                stats["trend"] = "stable"

        # Threshold analysis
        if request.threshold is not None:
            exceeding = [v for v in values if v > request.threshold]
            stats["threshold"] = request.threshold
            stats["threshold_violations"] = len(exceeding)
            stats["threshold_violation_pct"] = round(len(exceeding) / len(values) * 100, 1)

    metric_descriptions = [
        f"Metric: {request.metric_name}",
        f"Labels: {request.labels}" if request.labels else "No labels",
        f"Unit: {request.unit}" if request.unit else "Unit: not specified",
        f"Data points: {stats.get('data_points', 0)}",
        f"Range: {stats.get('min')} to {stats.get('max')}",
        f"Average: {stats.get('avg')}",
        f"Trend: {stats.get('trend', 'unknown')}",
    ]

    if request.query:
        metric_descriptions.append(f"Query: {request.query}")
    if request.threshold is not None:
        metric_descriptions.append(
            f"Threshold: {request.threshold} "
            f"(violations: {stats.get('threshold_violations', 0)}/"
            f"{stats.get('data_points', 0)})"
        )

    logger.info(
        "Normalized explain_metrics request",
        metric_name=request.metric_name,
        data_points=len(values),
        trend=stats.get("trend"),
    )

    return NormalizedData(
        data_type="metric_detail",
        source="grafana",
        time_range={"start": request.time_range.start, "end": request.time_range.end},
        summary_stats=stats,
        metric_descriptions=metric_descriptions,
        labels=request.labels,
    )
