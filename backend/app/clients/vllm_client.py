"""
vLLM client implementation using OpenAI-compatible API.

vLLM exposes an OpenAI-compatible API at /v1/chat/completions,
allowing us to use the official OpenAI Python SDK as the client.
This provides a clean, well-maintained interface with automatic
request/response serialization.

vLLM docs: https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html
"""

from openai import AsyncOpenAI

from app.clients.base import ModelClient
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VLLMClient(ModelClient):
    """
    Client for vLLM using its OpenAI-compatible API.
    
    Uses the official OpenAI Python SDK pointed at the vLLM server.
    This approach gives us automatic handling of streaming, retries,
    and response parsing through the well-tested OpenAI SDK.
    
    Attributes:
        base_url: vLLM server URL (default: http://localhost:8000/v1)
        model: Model name as loaded in vLLM
        api_key: API key (vLLM accepts any string if auth is disabled)
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ):
        self._base_url = (base_url or settings.VLLM_BASE_URL).rstrip("/")
        self._model = model or settings.VLLM_MODEL
        self._api_key = api_key or settings.VLLM_API_KEY
        self._timeout = timeout or settings.VLLM_TIMEOUT

        # Initialize the OpenAI async client pointed at vLLM
        self._client = AsyncOpenAI(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=self._timeout,
        )

        logger.info(
            "VLLMClient initialized",
            base_url=self._base_url,
            model=self._model,
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
        Send a chat completion request to vLLM's OpenAI-compatible endpoint.
        
        Uses the chat/completions format with system and user messages.
        This allows the model to properly distinguish between instructions
        (system prompt) and the data to analyze (user prompt).
        
        Args:
            prompt: User prompt with observability data.
            system_prompt: SRE assistant system prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum response tokens.
        
        Returns:
            Generated text from the model.
        
        Raises:
            openai.APIError: On vLLM API errors.
            openai.APITimeoutError: On request timeout.
        """
        logger.debug(
            "Sending vLLM chat completion request",
            model=self._model,
            prompt_length=len(prompt),
        )

        completion = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract the generated text from the first choice
        generated_text = completion.choices[0].message.content or ""

        logger.debug(
            "vLLM response received",
            model=self._model,
            response_length=len(generated_text),
            usage_prompt_tokens=completion.usage.prompt_tokens if completion.usage else None,
            usage_completion_tokens=completion.usage.completion_tokens if completion.usage else None,
        )

        return generated_text

    async def _do_health_check(self) -> bool:
        """
        Check vLLM connectivity by listing available models.
        
        The /v1/models endpoint returns the list of models loaded
        in the vLLM server. We verify our configured model is present.
        
        Returns:
            True if vLLM is reachable.
        """
        try:
            models = await self._client.models.list()
            available = [m.id for m in models.data]

            model_found = self._model in available
            if not model_found:
                logger.warning(
                    "Configured model not found in vLLM",
                    model=self._model,
                    available_models=available,
                )

            return True  # Server is reachable

        except Exception as e:
            logger.error("vLLM health check failed", error=str(e))
            return False

    async def close(self) -> None:
        """Close the OpenAI client."""
        await self._client.close()
        logger.info("VLLMClient closed")
