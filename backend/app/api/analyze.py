"""
POST /analyze endpoint.

Accepts dashboard metrics from Grafana, normalizes the payload,
builds a prompt, queries the LLM, and returns structured insights.
"""

import time

from fastapi import APIRouter, Depends, Request

from app.models.requests import AnalyzeRequest
from app.models.responses import InsightResponse
from app.dependencies import verify_api_key, get_llm_client, get_request_id
from app.clients.base import ModelClient
from app.services.normalizer import normalize_analyze_request
from app.services.prompt_builder import get_system_prompt, build_analyze_prompt
from app.services.response_formatter import format_response
from app.services.cache import cache_get, cache_set
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/analyze",
    response_model=InsightResponse,
    summary="Analyze Dashboard Metrics",
    description="Analyze Grafana dashboard metrics and return structured observability insights.",
    tags=["Analysis"],
)
async def analyze(
    payload: AnalyzeRequest,
    request: Request,
    _api_key: str = Depends(verify_api_key),
) -> InsightResponse:
    """
    Main analysis endpoint for Grafana dashboard data.

    Pipeline:
    1. Check cache for identical previous request
    2. Normalize the Grafana payload into internal format
    3. Build the LLM prompt with metric descriptions and stats
    4. Query the LLM and parse the structured response
    5. Cache and return the result
    """
    request_id = get_request_id(request)
    start = time.perf_counter()

    logger.info(
        "Analyze request received",
        source=payload.source,
        metric_count=len(payload.metrics),
        request_id=request_id,
    )

    # Step 1: Check cache
    cache_key_data = payload.model_dump()
    cached = cache_get(cache_key_data)
    if cached:
        logger.info("Returning cached response", request_id=request_id)
        result = InsightResponse(**cached)
        result.request_id = request_id
        result.cached = True
        return result

    # Step 2: Normalize
    normalized = normalize_analyze_request(payload)

    # Step 3: Build prompt
    system_prompt = get_system_prompt()
    user_prompt = build_analyze_prompt(normalized)

    # Step 4: Query LLM
    client = get_llm_client()
    raw_response = await client.generate(user_prompt, system_prompt)

    # Step 5: Format response
    duration_ms = int((time.perf_counter() - start) * 1000)
    result = format_response(
        raw_text=raw_response,
        request_id=request_id,
        model_name=client.model_name,
        processing_time_ms=duration_ms,
    )

    # Cache the result
    cache_set(cache_key_data, result.model_dump())

    logger.info(
        "Analyze request completed",
        request_id=request_id,
        duration_ms=duration_ms,
        severity=result.severity,
    )

    return result
