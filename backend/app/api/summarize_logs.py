"""
POST /summarize_logs endpoint.

Accepts log entries from Kibana, normalizes and chunks them,
builds a prompt, queries the LLM, and returns structured insights.
"""

import time

from fastapi import APIRouter, Depends, Request

from app.models.requests import SummarizeLogsRequest
from app.models.responses import InsightResponse
from app.dependencies import verify_api_key, get_llm_client, get_request_id
from app.services.normalizer import normalize_logs_request
from app.services.prompt_builder import get_system_prompt, build_summarize_logs_prompt
from app.services.response_formatter import format_response
from app.services.cache import cache_get, cache_set
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/summarize_logs",
    response_model=InsightResponse,
    summary="Summarize Logs",
    description="Summarize log entries from Kibana and identify issues, patterns, and anomalies.",
    tags=["Analysis"],
)
async def summarize_logs(
    payload: SummarizeLogsRequest,
    request: Request,
    _api_key: str = Depends(verify_api_key),
) -> InsightResponse:
    """
    Log summarization endpoint for Kibana data.

    Pipeline:
    1. Check cache
    2. Normalize logs (group by level, compute distribution)
    3. Build prompt with chunked logs (errors prioritized)
    4. Query LLM
    5. Format, cache, and return
    """
    request_id = get_request_id(request)
    start = time.perf_counter()

    logger.info(
        "Summarize logs request received",
        source=payload.source,
        log_count=len(payload.logs),
        request_id=request_id,
    )

    # Check cache
    cache_key_data = payload.model_dump()
    cached = cache_get(cache_key_data)
    if cached:
        logger.info("Returning cached log summary", request_id=request_id)
        result = InsightResponse(**cached)
        result.request_id = request_id
        result.cached = True
        return result

    # Normalize
    normalized = normalize_logs_request(payload)

    # Build prompt
    system_prompt = get_system_prompt()
    user_prompt = build_summarize_logs_prompt(normalized)

    # Query LLM
    client = get_llm_client()
    raw_response = await client.generate(user_prompt, system_prompt)

    # Format response
    duration_ms = int((time.perf_counter() - start) * 1000)
    result = format_response(
        raw_text=raw_response,
        request_id=request_id,
        model_name=client.model_name,
        processing_time_ms=duration_ms,
    )

    cache_set(cache_key_data, result.model_dump())

    logger.info(
        "Summarize logs completed",
        request_id=request_id,
        duration_ms=duration_ms,
        severity=result.severity,
    )

    return result
