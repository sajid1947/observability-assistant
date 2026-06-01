"""Tests for the Ollama client (mocked HTTP)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.clients.ollama_client import OllamaClient


@pytest.mark.asyncio
async def test_ollama_generate_success():
    """Test successful generate call."""
    client = OllamaClient(base_url="http://localhost:11434", model="test-model")

    mock_response = MagicMock()
    mock_response.json.return_value = {"response": '{"summary": "test"}'}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
        result = await client._do_generate("test prompt", "system prompt", 0.1, 1024)
        assert result == '{"summary": "test"}'

    await client.close()


@pytest.mark.asyncio
async def test_ollama_health_check_success():
    """Test successful health check."""
    client = OllamaClient(base_url="http://localhost:11434")

    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "qwen3:8b"}]}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_response):
        result = await client._do_health_check()
        assert result is True

    await client.close()


@pytest.mark.asyncio
async def test_ollama_health_check_failure():
    """Test health check when server is unreachable."""
    client = OllamaClient(base_url="http://localhost:11434")

    with patch.object(client._client, "get", new_callable=AsyncMock, side_effect=Exception("Connection refused")):
        result = await client._do_health_check()
        assert result is False

    await client.close()
