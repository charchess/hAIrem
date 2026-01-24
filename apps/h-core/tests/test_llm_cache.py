import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.infrastructure.llm import LlmClient

@pytest.mark.asyncio
async def test_llm_get_embedding_with_cache():
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None
    
    client = LlmClient(cache=mock_cache)
    
    # 1. Test Cache Miss
    with patch("src.infrastructure.llm.aembedding", new_callable=AsyncMock) as mock_aembedding:
        mock_aembedding.return_value = MagicMock(data=[{"embedding": [0.1, 0.2]}])
        
        emb = await client.get_embedding("test")
        
        assert emb == [0.1, 0.2]
        mock_cache.get.assert_called_once_with("test")
        mock_aembedding.assert_called_once()
        mock_cache.set.assert_called_once_with("test", [0.1, 0.2])

    # 2. Test Cache Hit
    mock_cache.get.reset_mock()
    mock_cache.set.reset_mock()
    mock_cache.get.return_value = [0.1, 0.2]
    
    with patch("src.infrastructure.llm.aembedding", new_callable=AsyncMock) as mock_aembedding:
        emb = await client.get_embedding("test")
        
        assert emb == [0.1, 0.2]
        mock_cache.get.assert_called_once_with("test")
        mock_aembedding.assert_not_called() # SHOULD NOT call provider
        mock_cache.set.assert_not_called() # SHOULD NOT set again
