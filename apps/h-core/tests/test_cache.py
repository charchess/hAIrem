import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.infrastructure.cache import EmbeddingCache

@pytest.fixture
def mock_redis():
    mock = MagicMock()
    mock.client = AsyncMock()
    return mock

@pytest.mark.asyncio
async def test_cache_set_get(mock_redis):
    cache = EmbeddingCache(mock_redis)
    text = "Hello World"
    vector = [0.1, 0.2, 0.3]
    
    # 1. Test SET
    await cache.set(text, vector)
    mock_redis.client.set.assert_called_once()
    
    # 2. Test GET (Hit)
    mock_redis.client.get.return_value = '[0.1, 0.2, 0.3]'
    result = await cache.get(text)
    assert result == vector
    
    # 3. Test GET (Miss)
    mock_redis.client.get.return_value = None
    result = await cache.get("Unknown")
    assert result is None

@pytest.mark.asyncio
async def test_cache_hashing(mock_redis):
    cache = EmbeddingCache(mock_redis)
    # Check that different cases result in the same key (normalization)
    key1 = cache._get_key("  Hello  ")
    key2 = cache._get_key("hello")
    assert key1 == key2
    assert "hairem:cache:emb:" in key1
