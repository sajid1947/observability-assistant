"""
POST /explain_metrics endpoint.

Accepts a single metric's time-series data for detailed explanation
including anomaly detection, trend analysis, and threshold evaluation.
"""

import time

from fastapi import APIRouter, Depends, Request

from app.models.requests import ExplainMetricsRequest
from app.models.responses import InsightResponse
from app.dependencies import verify_api_key, get_llm_client, get_request_id
from app.services.normalizer import normalize_explain_metrics_request
from app.services.prompt_builder import get_system_prompt, build_explain_metric_prompt
from app.services.response_formatter import format_response
from app.services.cache import cache_get, cache_set
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/explain_metrics",
    response_model=InsightResponse,
    summary="Explain Metric Behavior",
    description="Provide a detailed explanation of a specific metric's behavior and trends.",
    tags=["Analysis"],
)
async def explain_metrics(
    payload: ExplainMetricsRequest,
    request: Request,
    _api_key: str = Depends(verify_api_key),
) -> InsightResponse:
    """
    Metric explanation endpoint for detailed single-metric analysis.

    Pipeline:
    1. Check cache
    2. Normalize (compute stats, detect trends, check thresholds)
    3. Build prompt with detailed metric context
    4. Query LLM
    5. Format, cache, and return
    """
    request_id = get_request_id(request)
    start = time.perf_counter()

    logger.info(
        "Explain metrics request received",
        metric_name=payload.metric_name,
        data_points=len(payload.values),
        request_id=request_id,
    )

    # Check cache
    cache_key_data = payload.model_dump()
    cached = cache_get(cache_key_data)
    if cached:
        logger.info("Returning cached metric explanation", request_id=request_id)
        result = InsightResponse(**cached)
        result.request_id = request_id
        result.cached = True
        return result

    # Normalize
    normalized = normalize_explain_metrics_request(payload)

    # Build prompt
    system_prompt = get_system_prompt()
    user_prompt = build_explain_metric_prompt(normalized)

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
        "Explain metrics completed",
        request_id=request_id,
        duration_ms=duration_ms,
        severity=result.severity,
    )

    return result
