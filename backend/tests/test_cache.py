"""Tests for the cache service."""

from app.services.cache import cache_get, cache_set, cache_clear, get_cache_stats


def setup_function():
    """Clear cache before each test."""
    cache_clear()


def test_cache_miss():
    """Test that a new payload returns None."""
    result = cache_get({"key": "value"})
    assert result is None


def test_cache_hit():
    """Test that a cached payload is returned."""
    payload = {"key": "test"}
    response = {"summary": "cached result"}
    cache_set(payload, response)
    result = cache_get(payload)
    assert result == response


def test_cache_different_payloads():
    """Test that different payloads have different cache entries."""
    cache_set({"a": 1}, {"result": "first"})
    cache_set({"b": 2}, {"result": "second"})
    assert cache_get({"a": 1})["result"] == "first"
    assert cache_get({"b": 2})["result"] == "second"


def test_cache_stats():
    """Test cache statistics reporting."""
    cache_set({"x": 1}, {"result": "test"})
    cache_get({"x": 1})  # hit
    cache_get({"y": 2})  # miss
    stats = get_cache_stats()
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1
    assert stats["current_size"] >= 1


def test_cache_clear():
    """Test that clearing the cache removes all entries."""
    cache_set({"a": 1}, {"r": "x"})
    cache_clear()
    assert cache_get({"a": 1}) is None
