"""
Input sanitization utilities.

Provides functions to clean and validate user-supplied input before
processing. Prevents injection attacks and ensures data stays within
expected bounds. Used by API endpoints before passing data to services.
"""

import re
import html
from typing import Any


# Regex to match HTML/script tags
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>", re.DOTALL)

# Regex to match common script injection patterns
_SCRIPT_PATTERN = re.compile(
    r"(javascript:|on\w+\s*=|<script|<\/script|eval\(|document\.|window\.)",
    re.IGNORECASE,
)


def sanitize_string(value: str, max_length: int = 10_000) -> str:
    """
    Sanitize a string input by removing HTML tags, escaping special
    characters, and enforcing a maximum length.
    
    Args:
        value: Raw string input to sanitize.
        max_length: Maximum allowed string length. Truncates if exceeded.
    
    Returns:
        Sanitized string safe for processing and prompt inclusion.
    """
    if not isinstance(value, str):
        return str(value)[:max_length]

    # Strip HTML tags
    cleaned = _HTML_TAG_PATTERN.sub("", value)

    # Remove script injection patterns
    cleaned = _SCRIPT_PATTERN.sub("", cleaned)

    # HTML-escape remaining special characters
    cleaned = html.escape(cleaned, quote=True)

    # Enforce max length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned.strip()


def sanitize_log_entry(entry: str, max_length: int = 2000) -> str:
    """
    Sanitize a single log entry. Less aggressive than general sanitization
    since logs may legitimately contain special characters, but still
    enforces length limits and removes obvious injection attempts.
    
    Args:
        entry: Raw log line.
        max_length: Maximum allowed length per log entry.
    
    Returns:
        Sanitized log entry.
    """
    if not isinstance(entry, str):
        return str(entry)[:max_length]

    # Remove script tags but keep other angle brackets (common in logs)
    cleaned = re.sub(r"</?script[^>]*>", "", entry, flags=re.IGNORECASE)

    # Enforce max length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "... [truncated]"

    return cleaned


def sanitize_dict(data: dict[str, Any], max_depth: int = 5, _current_depth: int = 0) -> dict[str, Any]:
    """
    Recursively sanitize all string values in a dictionary.
    Prevents deeply nested payloads from causing stack overflows.
    
    Args:
        data: Dictionary to sanitize.
        max_depth: Maximum nesting depth to process.
        _current_depth: Internal tracker for recursion depth.
    
    Returns:
        Dictionary with all string values sanitized.
    """
    if _current_depth >= max_depth:
        return {"_error": "Max nesting depth exceeded"}

    sanitized: dict[str, Any] = {}
    for key, value in data.items():
        # Sanitize the key itself
        clean_key = sanitize_string(str(key), max_length=256)

        if isinstance(value, str):
            sanitized[clean_key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[clean_key] = sanitize_dict(value, max_depth, _current_depth + 1)
        elif isinstance(value, list):
            sanitized[clean_key] = [
                sanitize_string(item) if isinstance(item, str)
                else sanitize_dict(item, max_depth, _current_depth + 1) if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            sanitized[clean_key] = value

    return sanitized


def validate_payload_size(payload: bytes | str, max_size: int = 10_000_000) -> bool:
    """
    Check if a payload is within the allowed size limit.
    
    Args:
        payload: Raw payload (bytes or string).
        max_size: Maximum allowed size in bytes (default 10MB).
    
    Returns:
        True if within limits, False otherwise.
    """
    size = len(payload) if isinstance(payload, bytes) else len(payload.encode("utf-8"))
    return size <= max_size
