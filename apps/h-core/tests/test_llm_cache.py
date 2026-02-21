import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.infrastructure.llm import LlmClient


@pytest.mark.asyncio
async def test_llm_get_embedding_with_cache():
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None

    client = LlmClient(cache=mock_cache)

    # 1. Test Cache Miss
    # Mock the internal embedding_model
    client.embedding_model = MagicMock()
    client.embedding_model.embed.return_value = iter([[0.1, 0.2]])

    emb = await client.get_embedding("test")

    assert emb == [0.1, 0.2]
    mock_cache.get.assert_called_once_with("test")
    client.embedding_model.embed.assert_called_once()
    mock_cache.set.assert_called_once_with("test", [0.1, 0.2])

    # 2. Test Cache Hit
    mock_cache.get.reset_mock()
    mock_cache.set.reset_mock()
    mock_cache.get.return_value = [0.1, 0.2]
    client.embedding_model.embed.reset_mock()

    emb = await client.get_embedding("test")

    assert emb == [0.1, 0.2]
    mock_cache.get.assert_called_once_with("test")
    client.embedding_model.embed.assert_not_called()  # SHOULD NOT call model
    mock_cache.set.assert_not_called()  # SHOULD NOT set again
