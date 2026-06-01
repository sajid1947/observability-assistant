"""
Health check endpoint.

GET /health — Returns service status, LLM connectivity, uptime, and cache stats.
This endpoint is NOT behind API key auth so monitoring tools can access it.
"""

import time

from fastapi import APIRouter, Depends

from app.models.responses import HealthResponse
from app.config import settings
from app.dependencies import get_llm_client
from app.clients.base import ModelClient
from app.services.cache import get_cache_stats

router = APIRouter()

# Track service start time for uptime calculation
_start_time = time.monotonic()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns service health, LLM connectivity, and cache statistics.",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for monitoring and load balancers.

    Checks:
    1. Service is running (always true if this responds)
    2. LLM backend connectivity (calls health_check on the client)
    3. Reports uptime and cache statistics
    """
    uptime = time.monotonic() - _start_time

    # Check LLM connectivity
    try:
        client = get_llm_client()
        llm_health = await client.health_check()
        llm_status = llm_health.get("status", "unavailable")
        model_loaded = llm_health.get("model")
    except Exception:
        llm_status = "unavailable"
        model_loaded = None

    overall_status = "healthy" if llm_status == "connected" else "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        uptime_seconds=round(uptime, 2),
        llm_backend=settings.LLM_BACKEND,
        llm_status=llm_status,
        model_loaded=model_loaded,
        cache_stats=get_cache_stats(),
    )
