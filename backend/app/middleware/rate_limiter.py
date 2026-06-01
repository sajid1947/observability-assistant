"""
Token bucket rate limiter middleware.

Implements per-IP rate limiting using an in-memory token bucket.
Returns HTTP 429 with Retry-After header when the limit is exceeded.
"""

import time
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TokenBucket:
    """Simple token bucket for rate limiting a single client."""

    def __init__(self, max_tokens: int, refill_seconds: int):
        self.max_tokens = max_tokens
        self.refill_seconds = refill_seconds
        self.tokens = float(max_tokens)
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        """Try to consume one token. Returns True if allowed, False if rate limited."""
        now = time.monotonic()
        elapsed = now - self.last_refill

        # Refill tokens based on elapsed time
        self.tokens = min(
            self.max_tokens,
            self.tokens + elapsed * (self.max_tokens / self.refill_seconds),
        )
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    @property
    def retry_after(self) -> int:
        """Seconds until the next token is available."""
        if self.tokens >= 1:
            return 0
        tokens_needed = 1 - self.tokens
        return int(tokens_needed * self.refill_seconds / self.max_tokens) + 1


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Per-IP rate limiting middleware using token bucket algorithm.

    Exempt paths: /health, /docs, /openapi.json (monitoring and docs
    should never be rate limited).
    """

    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app: Any, **kwargs: Any):
        super().__init__(app, **kwargs)
        self._buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(settings.RATE_LIMIT_REQUESTS, settings.RATE_LIMIT_WINDOW)
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For for proxied setups."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        bucket = self._buckets[client_ip]

        if not bucket.consume():
            retry_after = bucket.retry_after
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                path=request.url.path,
                retry_after=retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": f"Too many requests. Retry after {retry_after} seconds.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
