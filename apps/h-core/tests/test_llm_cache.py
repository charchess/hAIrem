import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.llm import LlmClient, EMBEDDING_MODEL_NAME


@pytest.mark.asyncio
async def test_llm_get_embedding_cache_miss_then_store():
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None

    client = LlmClient(cache=mock_cache)
    client.embedding_model = MagicMock()
    client.embedding_model.embed.return_value = iter([[0.1, 0.2]])

    emb = await client.get_embedding("test")

    assert emb == [0.1, 0.2]
    mock_cache.get.assert_called_once_with("test", EMBEDDING_MODEL_NAME)
    client.embedding_model.embed.assert_called_once()
    mock_cache.set.assert_called_once_with("test", [0.1, 0.2], EMBEDDING_MODEL_NAME)


@pytest.mark.asyncio
async def test_llm_get_embedding_cache_hit_skips_model():
    mock_cache = AsyncMock()
    mock_cache.get.return_value = [0.1, 0.2]

    client = LlmClient(cache=mock_cache)
    client.embedding_model = MagicMock()

    emb = await client.get_embedding("test")

    assert emb == [0.1, 0.2]
    mock_cache.get.assert_called_once_with("test", EMBEDDING_MODEL_NAME)
    client.embedding_model.embed.assert_not_called()
    mock_cache.set.assert_not_called()
