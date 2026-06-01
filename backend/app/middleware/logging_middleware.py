"""
Structured request logging middleware.

Logs every request/response with method, path, status code, duration,
and request ID. Uses structlog for consistent JSON output.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.utils.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs each HTTP request with timing information.

    Logs include: method, path, status_code, duration_ms, client_ip.
    The request_id is automatically included via structlog context vars.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()

        # Log the incoming request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(
                "Request failed with exception",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Log the completed request
        log_method = logger.info if response.status_code < 400 else logger.warning
        log_method(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # Add timing header
        response.headers["X-Process-Time-Ms"] = str(duration_ms)

        return response
