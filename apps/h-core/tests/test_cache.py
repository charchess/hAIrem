import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.cache import EmbeddingCache

MODEL_A = "vendor/model-a"
MODEL_B = "vendor/model-b"


@pytest.fixture
def mock_redis():
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_cache_set_get(mock_redis):
    cache = EmbeddingCache(mock_redis)
    text = "Hello World"
    vector = [0.1, 0.2, 0.3]

    await cache.set(text, vector, MODEL_A)
    mock_redis.set.assert_called_once()

    mock_redis.get.return_value = [0.1, 0.2, 0.3]
    result = await cache.get(text, MODEL_A)
    assert result == vector

    mock_redis.get.return_value = None
    result = await cache.get("Unknown", MODEL_A)
    assert result is None


@pytest.mark.asyncio
async def test_cache_hashing_normalizes_whitespace_and_case(mock_redis):
    cache = EmbeddingCache(mock_redis)
    key1 = cache._get_key("  Hello  ", MODEL_A)
    key2 = cache._get_key("hello", MODEL_A)
    assert key1 == key2
    assert "hairem:cache:emb:" in key1


@pytest.mark.asyncio
async def test_cache_key_isolated_per_model(mock_redis):
    cache = EmbeddingCache(mock_redis)
    text = "shared text"
    key_a = cache._get_key(text, MODEL_A)
    key_b = cache._get_key(text, MODEL_B)
    assert key_a != key_b
    assert "vendor_model-a" in key_a
    assert "vendor_model-b" in key_b


@pytest.mark.asyncio
async def test_cache_skip_empty_vector(mock_redis):
    cache = EmbeddingCache(mock_redis)
    await cache.set("any text", [], MODEL_A)
    mock_redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_cache_get_returns_none_on_non_list(mock_redis):
    cache = EmbeddingCache(mock_redis)
    mock_redis.get.return_value = "not-a-list"
    result = await cache.get("text", MODEL_A)
    assert result is None


@pytest.mark.asyncio
async def test_cache_get_degrades_on_redis_error(mock_redis):
    cache = EmbeddingCache(mock_redis)
    mock_redis.get.side_effect = Exception("Redis down")
    result = await cache.get("text", MODEL_A)
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_degrades_on_redis_error(mock_redis):
    cache = EmbeddingCache(mock_redis)
    mock_redis.set.side_effect = Exception("Redis down")
    await cache.set("text", [0.1], MODEL_A)
