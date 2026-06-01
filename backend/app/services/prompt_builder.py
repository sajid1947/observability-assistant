"""
Prompt engineering service.

Constructs system and user prompts for the LLM based on the
normalized observability data.
"""

from app.services.normalizer import NormalizedData
from app.services.chunker import chunk_logs, format_chunks_for_prompt
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE).
Your task is to analyze scraped text from a Grafana/Kibana dashboard and identify potential system issues.

CRITICAL INSTRUCTION: You MUST return ONLY a single, valid JSON object. Do not include markdown formatting (like ```json), backticks, or any explanatory text whatsoever. Start your response with { and end with }.

The JSON object must strictly follow this schema:
{
    "summary": "1-2 sentences explaining exactly what the data indicates.",
    "root_cause": "Hypothesize the root cause if anomalies exist, otherwise state 'System operating normally'.",
    "severity": "critical", // Must be one of: critical, high, medium, low, info
    "confidence": "90%",
    "evidence": ["Data point 1 from the text", "Data point 2 from the text"],
    "recommendations": ["Actionable step 1", "Actionable step 2"],
    "anomalies_detected": ["List any sudden spikes, drops, or errors found"]
}

Rules:
- Base your analysis ONLY on the provided dashboard text. Do not hallucinate.
- If the data looks like normal metrics without errors, mark severity as 'info' and root_cause as 'System operating normally'.
- Do NOT output any words outside of the JSON object."""

ANALYZE_METRICS_TEMPLATE = """Analyze the following dashboard metrics and provide an observability insight.

## Context
- Source: {source}
- Time Range: {time_start} to {time_end}
{extra_context}

## Metrics ({metric_count} total)
{metrics_section}

Analyze these metrics for anomalies, correlations, potential issues, and trends.
Return your analysis as the specified JSON format."""

SUMMARIZE_LOGS_TEMPLATE = """Summarize the following log entries and identify any issues.

## Context
- Source: {source}
- Time Range: {time_start} to {time_end}
{extra_context}

## Log Statistics
- Total log entries: {total_logs}
- Level distribution: {level_distribution}

## Log Entries
{logs_section}

Analyze these logs for error patterns, root causes, recurring issues, and anomalous entries.
Return your analysis as the specified JSON format."""

EXPLAIN_METRIC_TEMPLATE = """Explain the behavior of the following metric in detail.

## Metric Details
- Name: {metric_name}
{metric_details}

## Time Range: {time_start} to {time_end}

## Data Summary
{data_summary}

Explain what this metric indicates, whether values are normal or anomalous,
any trends, potential impact, and recommended actions.
Return your analysis as the specified JSON format."""


def get_system_prompt() -> str:
    """Return the SRE assistant system prompt."""
    return SYSTEM_PROMPT


def build_analyze_prompt(data: NormalizedData) -> str:
    """Build a user prompt for metric analysis (POST /analyze)."""
    metrics_section = "\n".join(f"- {d}" for d in data.metric_descriptions) or "- No data"
    extra_context = ""
    if data.raw_context:
        extra_context = f"\n{data.raw_context}"
    if data.labels:
        extra_context += f"\n- Labels: {data.labels}"

    prompt = ANALYZE_METRICS_TEMPLATE.format(
        source=data.source,
        time_start=data.time_range.get("start", "unknown"),
        time_end=data.time_range.get("end", "unknown"),
        extra_context=extra_context,
        metric_count=len(data.metric_descriptions),
        metrics_section=metrics_section,
    )
    logger.debug("Built analyze prompt", prompt_length=len(prompt))
    return prompt


def build_summarize_logs_prompt(data: NormalizedData) -> str:
    """Build a user prompt for log summarization (POST /summarize_logs)."""
    chunks = chunk_logs(data.log_summaries)
    formatted_chunks = format_chunks_for_prompt(chunks)

    if len(formatted_chunks) <= 1:
        logs_section = formatted_chunks[0] if formatted_chunks else "No logs"
    else:
        logs_section = formatted_chunks[0]
        logs_section += f"\n\n[Note: {len(chunks)-1} additional chunks not shown.]"

    level_dist = data.summary_stats.get("level_distribution", {})
    level_str = ", ".join(f"{k}: {v}" for k, v in level_dist.items()) or "unknown"
    extra_context = f"\n{data.raw_context}" if data.raw_context else ""

    prompt = SUMMARIZE_LOGS_TEMPLATE.format(
        source=data.source,
        time_start=data.time_range.get("start", "unknown"),
        time_end=data.time_range.get("end", "unknown"),
        extra_context=extra_context,
        total_logs=data.summary_stats.get("total_logs", 0),
        level_distribution=level_str,
        logs_section=logs_section,
    )
    logger.debug("Built summarize_logs prompt", prompt_length=len(prompt))
    return prompt


def build_explain_metric_prompt(data: NormalizedData) -> str:
    """Build a user prompt for metric explanation (POST /explain_metrics)."""
    metric_details = "\n".join(f"- {d}" for d in data.metric_descriptions)
    stats = data.summary_stats

    data_summary_parts = [
        f"- Data points: {stats.get('data_points', 'N/A')}",
        f"- Min: {stats.get('min', 'N/A')}, Max: {stats.get('max', 'N/A')}",
        f"- Average: {stats.get('avg', 'N/A')}, Latest: {stats.get('latest', 'N/A')}",
        f"- Trend: {stats.get('trend', 'unknown')}",
    ]
    if "threshold" in stats:
        data_summary_parts.append(
            f"- Threshold: {stats['threshold']} "
            f"(violations: {stats.get('threshold_violations', 0)}, "
            f"{stats.get('threshold_violation_pct', 0)}%)"
        )

    prompt = EXPLAIN_METRIC_TEMPLATE.format(
        metric_name=stats.get("metric_name", "unknown"),
        metric_details=metric_details,
        time_start=data.time_range.get("start", "unknown"),
        time_end=data.time_range.get("end", "unknown"),
        data_summary="\n".join(data_summary_parts),
    )
    logger.debug("Built explain_metric prompt", prompt_length=len(prompt))
    return prompt
