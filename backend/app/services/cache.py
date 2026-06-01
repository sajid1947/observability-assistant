"""
TTL-based in-memory caching service.

Caches LLM responses keyed by a hash of the input payload.
Avoids redundant LLM calls for identical requests within the
TTL window. Uses cachetools for thread-safe TTL eviction.
"""

import hashlib
import json
from typing import Any, Optional

from cachetools import TTLCache

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level cache instance — shared across the application
_cache: TTLCache = TTLCache(
    maxsize=settings.CACHE_MAX_SIZE,
    ttl=settings.CACHE_TTL,
)

# Statistics counters
_stats = {"hits": 0, "misses": 0}


def _compute_key(data: dict[str, Any]) -> str:
    """
    Compute a deterministic cache key from a request payload.

    Uses SHA-256 of the JSON-serialized payload with sorted keys
    to ensure identical payloads always produce the same key,
    regardless of dict ordering.
    """
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def cache_get(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    Look up a cached response for the given payload.

    Returns:
        Cached response dict if found and not expired, None otherwise.
    """
    key = _compute_key(payload)
    result = _cache.get(key)

    if result is not None:
        _stats["hits"] += 1
        logger.debug("Cache hit", cache_key=key[:12])
        return result

    _stats["misses"] += 1
    logger.debug("Cache miss", cache_key=key[:12])
    return None


def cache_set(payload: dict[str, Any], response: dict[str, Any]) -> None:
    """
    Store a response in the cache keyed by the payload hash.
    """
    key = _compute_key(payload)
    _cache[key] = response
    logger.debug("Cache set", cache_key=key[:12], cache_size=len(_cache))


def cache_clear() -> None:
    """Clear all cached entries."""
    _cache.clear()
    logger.info("Cache cleared")


def get_cache_stats() -> dict[str, Any]:
    """
    Return cache statistics.

    Returns:
        Dict with hits, misses, hit_rate, current_size, and max_size.
    """
    total = _stats["hits"] + _stats["misses"]
    return {
        "hits": _stats["hits"],
        "misses": _stats["misses"],
        "hit_rate": f"{(_stats['hits'] / total * 100):.1f}%" if total > 0 else "0%",
        "current_size": len(_cache),
        "max_size": settings.CACHE_MAX_SIZE,
        "ttl_seconds": settings.CACHE_TTL,
    }
