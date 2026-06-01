"""
FastAPI dependency injection functions.

Provides reusable dependencies for authentication, request ID access,
and LLM client instantiation. These are injected into route handlers
via FastAPI's Depends() mechanism.
"""

from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import APIKeyHeader

from app.config import settings
from app.clients.base import ModelClient
from app.clients.ollama_client import OllamaClient
from app.clients.vllm_client import VLLMClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

# API key header scheme
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Singleton LLM client — initialized once, reused across requests
_llm_client: ModelClient | None = None


def get_llm_client() -> ModelClient:
    """
    Get or create the LLM client singleton.

    The client is created based on the LLM_BACKEND setting:
    - "ollama": Creates an OllamaClient
    - "vllm": Creates a VLLMClient

    Returns:
        The configured ModelClient instance.

    Raises:
        ValueError: If LLM_BACKEND is not recognized.
    """
    global _llm_client
    if _llm_client is None:
        if settings.LLM_BACKEND == "ollama":
            _llm_client = OllamaClient()
        elif settings.LLM_BACKEND == "vllm":
            _llm_client = VLLMClient()
        else:
            raise ValueError(f"Unknown LLM backend: {settings.LLM_BACKEND}")
        logger.info("LLM client initialized", backend=settings.LLM_BACKEND)
    return _llm_client


async def verify_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    """
    Validate the API key from the X-API-Key header.

    This dependency is injected into all protected endpoints.
    The key is compared against the configured API_KEY setting.

    Returns:
        The validated API key string.

    Raises:
        HTTPException 401: If the key is missing.
        HTTPException 403: If the key is invalid.
    """
    if api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key. Provide X-API-Key header.")
    if api_key != settings.API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(status_code=403, detail="Invalid API key.")
    return api_key


def get_request_id(request: Request) -> str:
    """
    Extract the request ID from request state (set by RequestIDMiddleware).

    Returns:
        The request ID string, or "unknown" if not set.
    """
    return getattr(request.state, "request_id", "unknown")
