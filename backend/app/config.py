"""
Application configuration using Pydantic Settings.

Loads settings from environment variables and .env file.
All config is centralized here for easy management and validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Environment variables take precedence over .env file values.
    All LLM, security, and performance settings are configured here.
    """

    # ──────────────────────────────────────────────
    # Application
    # ──────────────────────────────────────────────
    APP_NAME: str = "Observability Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ──────────────────────────────────────────────
    # LLM Configuration
    # ──────────────────────────────────────────────
    # Which backend to use: "ollama" or "vllm"
    LLM_BACKEND: str = Field(default="ollama", description="LLM backend: 'ollama' or 'vllm'")
    
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_TIMEOUT: int = Field(default=120, description="Timeout in seconds for Ollama requests")

    # vLLM settings (OpenAI-compatible)
    VLLM_BASE_URL: str = "http://localhost:8000/v1"
    VLLM_MODEL: str = "qwen3:8b"
    VLLM_API_KEY: str = "not-needed"
    VLLM_TIMEOUT: int = Field(default=120, description="Timeout in seconds for vLLM requests")

    # Model parameters
    MODEL_TEMPERATURE: float = Field(default=0.1, ge=0.0, le=2.0, description="Lower = more deterministic")
    MODEL_MAX_TOKENS: int = Field(default=2048, description="Max tokens in LLM response")

    # ──────────────────────────────────────────────
    # Security
    # ──────────────────────────────────────────────
    API_KEY: str = Field(default="dev-key-change-me-in-production", description="API key for authentication")
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5601", "http://localhost:8080"],
        description="Allowed CORS origins"
    )

    # ──────────────────────────────────────────────
    # Rate Limiting
    # ──────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = Field(default=30, description="Max requests per minute per IP")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")

    # ──────────────────────────────────────────────
    # Caching
    # ──────────────────────────────────────────────
    CACHE_TTL: int = Field(default=300, description="Cache TTL in seconds (5 minutes)")
    CACHE_MAX_SIZE: int = Field(default=256, description="Max number of cached responses")

    # ──────────────────────────────────────────────
    # Processing
    # ──────────────────────────────────────────────
    MAX_LOG_ENTRIES: int = Field(default=500, description="Max log entries to process per request")
    MAX_LOG_ENTRY_LENGTH: int = Field(default=2000, description="Max characters per log entry")
    CHUNK_SIZE: int = Field(default=4000, description="Max tokens per log chunk")
    MAX_PAYLOAD_SIZE: int = Field(default=10_000_000, description="Max request payload size in bytes (10MB)")

    # ──────────────────────────────────────────────
    # Retry Configuration
    # ──────────────────────────────────────────────
    RETRY_MAX_ATTEMPTS: int = Field(default=3, description="Max retry attempts for LLM calls")
    RETRY_BASE_DELAY: float = Field(default=1.0, description="Base delay in seconds for exponential backoff")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Singleton settings instance — import this everywhere
settings = Settings()
