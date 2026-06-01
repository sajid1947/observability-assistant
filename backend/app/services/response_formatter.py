"""
Response formatting service.

Parses raw LLM output into the structured InsightResponse model.
Handles malformed JSON gracefully by attempting multiple extraction
strategies before falling back to a best-effort response.
"""

import json
import re
from typing import Optional

from app.models.responses import InsightResponse, SeverityLevel
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _extract_json_from_text(text: str) -> Optional[dict]:
    """
    Attempt to extract a JSON object from raw LLM output.

    Tries multiple strategies:
    1. Direct JSON parse of the entire text
    2. Extract JSON from markdown code fences
    3. Find the first { ... } block via regex
    """
    # Strategy 1: Direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from code fences (```json ... ``` or ``` ... ```)
    fence_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(fence_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Strategy 3: Find first { ... } block (greedy, handles nested braces)
    brace_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    matches = re.findall(brace_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    return None


def _normalize_severity(value: str) -> SeverityLevel:
    """Map various severity strings to our enum values."""
    mapping = {
        "critical": SeverityLevel.CRITICAL,
        "crit": SeverityLevel.CRITICAL,
        "high": SeverityLevel.HIGH,
        "medium": SeverityLevel.MEDIUM,
        "med": SeverityLevel.MEDIUM,
        "low": SeverityLevel.LOW,
        "info": SeverityLevel.INFO,
        "informational": SeverityLevel.INFO,
        "warning": SeverityLevel.MEDIUM,
        "warn": SeverityLevel.MEDIUM,
    }
    return mapping.get(value.lower().strip(), SeverityLevel.INFO)


def format_response(
    raw_text: str,
    request_id: Optional[str] = None,
    model_name: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
    cached: bool = False,
) -> InsightResponse:
    """
    Parse raw LLM output into a structured InsightResponse.

    Attempts JSON extraction, validates fields, and falls back
    to a best-effort response if parsing fails entirely.
    """
    parsed = _extract_json_from_text(raw_text)

    if parsed and isinstance(parsed, dict):
        try:
            # Normalize severity
            raw_severity = parsed.get("severity", "info")
            severity = _normalize_severity(str(raw_severity))

            return InsightResponse(
                summary=str(parsed.get("summary", "Analysis complete")),
                root_cause=str(parsed.get("root_cause", "Unable to determine")),
                severity=severity,
                confidence=str(parsed.get("confidence", "N/A")),
                evidence=_ensure_string_list(parsed.get("evidence", [])),
                recommendations=_ensure_string_list(parsed.get("recommendations", [])),
                anomalies_detected=_ensure_string_list(parsed.get("anomalies_detected", [])),
                request_id=request_id,
                model_used=model_name,
                processing_time_ms=processing_time_ms,
                cached=cached,
            )
        except Exception as e:
            logger.warning("Failed to construct InsightResponse from parsed JSON", error=str(e))

    # Fallback: return the raw text as the summary
    logger.warning("Could not parse LLM output as JSON, using fallback", raw_length=len(raw_text))
    return InsightResponse(
        summary=raw_text[:1000] if raw_text else "No response from model",
        root_cause="Unable to parse structured response from model",
        severity=SeverityLevel.INFO,
        confidence="N/A",
        evidence=["Raw model output was not valid JSON"],
        recommendations=["Review raw model output for insights"],
        anomalies_detected=[],
        request_id=request_id,
        model_used=model_name,
        processing_time_ms=processing_time_ms,
        cached=cached,
    )


def _ensure_string_list(value: list | str | None) -> list[str]:
    """Ensure a value is a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
