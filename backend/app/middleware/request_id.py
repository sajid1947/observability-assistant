"""
Request ID middleware.

Generates a unique UUID4 for each request and attaches it to:
1. The response headers as X-Request-ID
2. The structlog context vars for automatic inclusion in all log messages
3. The request state for access in route handlers
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import structlog


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique request ID to every incoming request.

    If the client provides an X-Request-ID header, it is reused (useful
    for distributed tracing). Otherwise, a new UUID4 is generated.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Use client-provided ID or generate a new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in request state for route handlers
        request.state.request_id = request_id

        # Bind to structlog context so all logs in this request include it
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Process the request
        response = await call_next(request)

        # Include request ID in response headers
        response.headers["X-Request-ID"] = request_id

        return response
