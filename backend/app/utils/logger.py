"""
Structured JSON logging configuration using structlog.

Provides consistent, machine-parseable log output with automatic
context binding (request_id, timestamp, level). All application
modules should use `get_logger()` to obtain their logger instance.
"""

import logging
import sys
import structlog
from app.config import settings


def setup_logging() -> None:
    """
    Configure structlog for structured JSON logging.
    
    This should be called once at application startup (in main.py lifespan).
    It configures both structlog and the standard library logging to produce
    consistent JSON output suitable for log aggregation systems.
    """
    # Configure structlog processors pipeline
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,          # Merge context vars (e.g., request_id)
        structlog.stdlib.add_logger_name,                 # Add logger name
        structlog.stdlib.add_log_level,                   # Add log level
        structlog.processors.TimeStamper(fmt="iso"),      # ISO 8601 timestamps
        structlog.processors.StackInfoRenderer(),         # Stack info if present
        structlog.processors.format_exc_info,             # Format exception info
        structlog.processors.UnicodeDecoder(),            # Decode bytes to strings
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            # Final processor: render as JSON for production, console for debug
            structlog.dev.ConsoleRenderer()
            if settings.DEBUG
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to match
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the calling module).
              If None, returns an unbound logger.
    
    Returns:
        A bound structlog logger with automatic context propagation.
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Processing request", user_id=123, action="analyze")
    """
    return structlog.get_logger(name)
