"""
API router — aggregates all endpoint routers into a single router.
"""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.analyze import router as analyze_router
from app.api.summarize_logs import router as logs_router
from app.api.explain_metrics import router as metrics_router

# Main API router that includes all endpoint routers
api_router = APIRouter()

# Health check (no prefix, no auth)
api_router.include_router(health_router)

# Analysis endpoints
api_router.include_router(analyze_router)
api_router.include_router(logs_router)
api_router.include_router(metrics_router)
