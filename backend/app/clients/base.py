"""
Abstract base class for LLM model clients.

All LLM backends (Ollama, vLLM, etc.) implement this interface.
Provides built-in retry logic with exponential backoff, timeout
handling, and health checking. Concrete subclasses only need to
implement `_do_generate()` and `_do_health_check()`.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ModelClient(ABC):
    """
    Abstract model client with retry logic and health checking.
    
    Subclasses must implement:
        - _do_generate(): The actual LLM API call
        - _do_health_check(): Check if the backend is reachable
        - model_name property: Return the configured model name
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name of the configured model."""
        ...

    @abstractmethod
    async def _do_generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Execute the actual generation request against the LLM backend.
        
        Args:
            prompt: User prompt with the data to analyze.
            system_prompt: System prompt defining the assistant's behavior.
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens: Maximum tokens in the response.
        
        Returns:
            Raw text response from the LLM.
        
        Raises:
            Exception: On any API or network error.
        """
        ...

    @abstractmethod
    async def _do_health_check(self) -> bool:
        """
        Check connectivity to the LLM backend.
        
        Returns:
            True if the backend is reachable and responsive.
        """
        ...

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a response from the LLM with automatic retry logic.
        
        Implements exponential backoff: delay = base_delay * 2^attempt.
        Retries on transient errors (network, timeout, server errors).
        
        Args:
            prompt: User prompt text.
            system_prompt: System prompt text.
            temperature: Override for model temperature. Defaults to settings.
            max_tokens: Override for max tokens. Defaults to settings.
        
        Returns:
            Raw text response from the model.
        
        Raises:
            RuntimeError: If all retry attempts are exhausted.
        """
        temp = temperature if temperature is not None else settings.MODEL_TEMPERATURE
        tokens = max_tokens if max_tokens is not None else settings.MODEL_MAX_TOKENS
        last_error: Optional[Exception] = None

        for attempt in range(1, settings.RETRY_MAX_ATTEMPTS + 1):
            try:
                logger.info(
                    "LLM generation attempt",
                    attempt=attempt,
                    model=self.model_name,
                    max_attempts=settings.RETRY_MAX_ATTEMPTS,
                )
                response = await self._do_generate(prompt, system_prompt, temp, tokens)
                logger.info(
                    "LLM generation successful",
                    attempt=attempt,
                    model=self.model_name,
                    response_length=len(response),
                )
                return response

            except Exception as e:
                last_error = e
                logger.warning(
                    "LLM generation failed",
                    attempt=attempt,
                    model=self.model_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                # Don't sleep after the last attempt
                if attempt < settings.RETRY_MAX_ATTEMPTS:
                    delay = settings.RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.info("Retrying after delay", delay_seconds=delay)
                    await asyncio.sleep(delay)

        raise RuntimeError(
            f"LLM generation failed after {settings.RETRY_MAX_ATTEMPTS} attempts: {last_error}"
        )

    async def health_check(self) -> dict:
        """
        Perform a health check on the LLM backend.
        
        Returns:
            Dict with 'status' ('connected' or 'unavailable'),
            'model' name, and optional 'error' message.
        """
        try:
            is_healthy = await self._do_health_check()
            return {
                "status": "connected" if is_healthy else "unavailable",
                "model": self.model_name,
            }
        except Exception as e:
            logger.error("Health check failed", error=str(e), model=self.model_name)
            return {
                "status": "unavailable",
                "model": self.model_name,
                "error": str(e),
            }
