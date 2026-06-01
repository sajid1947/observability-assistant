"""
FastAPI application entry point.

Configures the application with:
- Lifespan handler for startup/shutdown (logging, LLM client)
- CORS middleware for Grafana/Kibana origins
- Custom middleware stack (request ID, rate limiting, logging)
- Global exception handlers
- API router registration
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.api.router import api_router
from app.dependencies import get_llm_client

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Startup: Initialize logging, warm up LLM client.
    Shutdown: Close LLM client connections.
    """
    # ── Startup ──
    setup_logging()
    logger.info(
        "Application starting",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        llm_backend=settings.LLM_BACKEND,
        debug=settings.DEBUG,
    )

    # Initialize the LLM client eagerly so startup failures surface early
    try:
        client = get_llm_client()
        health = await client.health_check()
        logger.info("LLM client initialized", health=health)
    except Exception as e:
        logger.error("Failed to initialize LLM client", error=str(e))
        # Don't crash — the service can still report health as degraded

    yield

    # ── Shutdown ──
    logger.info("Application shutting down")
    try:
        client = get_llm_client()
        if hasattr(client, "close"):
            await client.close()
    except Exception:
        pass


# ── Create the FastAPI application ──
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered observability assistant that analyzes metrics and logs "
        "from Grafana and Kibana using local LLMs (Ollama/vLLM)."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Middleware stack (order matters: last added = first executed) ──

# 1. CORS — must be outermost to handle preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
)

# 2. Request ID — assigns UUID to each request
app.add_middleware(RequestIDMiddleware)

# 3. Rate limiting — per-IP token bucket
app.add_middleware(RateLimiterMiddleware)

# 4. Logging — logs every request with timing
app.add_middleware(LoggingMiddleware)


# ── Global exception handlers ──

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler to prevent stack traces leaking to clients."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=request_id,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": "An internal error occurred. Check logs for details.",
            "request_id": request_id,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle validation errors that escape Pydantic."""
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": str(exc),
            "request_id": request_id,
        },
    )


# ── Register API routes ──
app.include_router(api_router)
