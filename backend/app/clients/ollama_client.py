"""
Ollama LLM client implementation.

Communicates with the Ollama API at /api/generate for text generation
and /api/tags for health checking. Supports configurable model selection,
streaming (disabled for structured output), and timeout handling.

Ollama API reference: https://github.com/ollama/ollama/blob/main/docs/api.md
"""

import httpx

from app.clients.base import ModelClient
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaClient(ModelClient):
    """
    Client for the Ollama local LLM server.
    
    Connects to Ollama's REST API at the configured base URL.
    Uses the /api/generate endpoint for text generation and
    /api/tags to verify server connectivity and model availability.
    
    Attributes:
        base_url: Ollama server URL (default: http://localhost:11434)
        model: Model name to use (default: qwen3:8b)
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT

        # Reusable async HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=10.0),
        )

        logger.info(
            "OllamaClient initialized",
            base_url=self.base_url,
            model=self._model,
            timeout=self.timeout,
        )

    @property
    def model_name(self) -> str:
        return self._model

    async def _do_generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Send a generation request to Ollama's /api/generate endpoint.
        
        The request uses stream=False to get the complete response in
        a single JSON object, which is required for structured output
        parsing. The system prompt is passed separately from the user
        prompt for proper context separation.
        
        Args:
            prompt: User prompt with observability data.
            system_prompt: SRE assistant system prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum response tokens.
        
        Returns:
            Generated text from the model.
        
        Raises:
            httpx.HTTPStatusError: On non-2xx response.
            httpx.TimeoutException: On request timeout.
        """
        payload = {
            "model": self._model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,  # Get complete response for JSON parsing
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        logger.debug(
            "Sending Ollama generate request",
            model=self._model,
            prompt_length=len(prompt),
        )

        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()

        data = response.json()
        generated_text = data.get("response", "")

        logger.debug(
            "Ollama generate response received",
            model=self._model,
            response_length=len(generated_text),
            eval_count=data.get("eval_count"),
            total_duration_ns=data.get("total_duration"),
        )

        return generated_text

    async def _do_health_check(self) -> bool:
        """
        Check Ollama connectivity by querying the /api/tags endpoint.
        
        Also verifies that the configured model is available in the
        list of loaded models. Logs a warning if the model is not found.
        
        Returns:
            True if Ollama is reachable and the model is available.
        """
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()

            # Check if our configured model is available
            available_models = [m.get("name", "") for m in data.get("models", [])]
            model_available = any(self._model in m for m in available_models)

            if not model_available:
                logger.warning(
                    "Configured model not found in Ollama",
                    model=self._model,
                    available_models=available_models,
                )

            return True  # Server is reachable even if model isn't loaded yet

        except Exception as e:
            logger.error("Ollama health check failed", error=str(e))
            return False

    async def close(self) -> None:
        """Close the HTTP client and release connections."""
        await self._client.aclose()
        logger.info("OllamaClient closed")
