import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.domain.memory import MemoryConsolidator

@pytest.mark.asyncio
async def test_memory_consolidation_no_messages():
    mock_surreal = AsyncMock()
    mock_surreal.get_unprocessed_messages.return_value = []
    
    consolidator = MemoryConsolidator(mock_surreal, AsyncMock(), AsyncMock())
    facts = await consolidator.consolidate()
    
    assert facts == 0
    mock_surreal.get_unprocessed_messages.assert_called_once()

@pytest.mark.asyncio
async def test_memory_consolidation_success():
    mock_surreal = AsyncMock()
    mock_llm = AsyncMock()
    mock_redis = AsyncMock()
    
    # Setup mock data
    mock_surreal.get_unprocessed_messages.return_value = [
        {"id": "messages:uuid1", "sender": {"agent_id": "user"}, "payload": {"content": "I love green tea"}},
        {"id": "messages:uuid2", "sender": {"agent_id": "Renarde"}, "payload": {"content": "Noted, green tea is great."}}
    ]
    
    # Mock LLM extraction
    mock_llm.get_completion.return_value = '[{"fact": "User likes green tea", "subject": "user", "agent": "Renarde", "confidence": 0.9}]'
    mock_llm.get_embedding.return_value = [0.1, 0.2]
    
    consolidator = MemoryConsolidator(mock_surreal, mock_llm, mock_redis)
    facts_count = await consolidator.consolidate()
    
    assert facts_count == 1
    # Check if messages were marked as processed
    mock_surreal.mark_as_processed.assert_called_once_with(["uuid1", "uuid2"])
    # Check if memory was inserted
    mock_surreal.insert_memory.assert_called_once()
    args, _ = mock_surreal.insert_memory.call_args
    assert args[0]["fact"] == "User likes green tea"
    assert args[0]["embedding"] == [0.1, 0.2]
    # Check if log was broadcasted
    mock_redis.publish.assert_called_once()
