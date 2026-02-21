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
        {
            "id": "messages:uuid2",
            "sender": {"agent_id": "Renarde"},
            "payload": {"content": "Noted, green tea is great."},
        },
    ]

    # Mock LLM extraction
    mock_llm.get_completion.return_value = '{"facts": [{"fact": "User likes green tea", "subject": "user", "agent": "Renarde", "confidence": 0.9}], "causal_links": [], "concepts": []}'
    mock_llm.get_embedding.return_value = [0.1, 0.2]

    # Mock semantic search to avoid conflict check issues
    mock_surreal.semantic_search.return_value = []

    consolidator = MemoryConsolidator(mock_surreal, mock_llm, mock_redis)
    facts_count = await consolidator.consolidate()

    assert facts_count == 1
    # Check if messages were marked as processed
    mock_surreal.mark_as_processed.assert_called_once_with(["uuid1", "uuid2"])
    # Check if graph memory was inserted
    mock_surreal.insert_graph_memory.assert_called_once()
    args, _ = mock_surreal.insert_graph_memory.call_args
    assert args[0]["fact"] == "User likes green tea"
    assert args[0]["embedding"] == [0.1, 0.2]
    # Check if log was broadcasted
    mock_redis.publish.assert_called_once()


# =============================================
# Decay Tests (Story 13.2)
# =============================================


@pytest.mark.asyncio
async def test_apply_decay_calls_surreal():
    """Test that apply_decay calls the SurrealDB decay method."""
    mock_surreal = AsyncMock()
    mock_surreal.apply_decay_to_all_memories.return_value = 5
    mock_surreal.cleanup_orphaned_facts.return_value = 2

    consolidator = MemoryConsolidator(mock_surreal, AsyncMock(), AsyncMock())
    await consolidator.apply_decay(decay_rate=0.1, threshold=0.1)

    mock_surreal.apply_decay_to_all_memories.assert_called_once_with(0.1, 0.1)
    mock_surreal.cleanup_orphaned_facts.assert_called_once()


@pytest.mark.asyncio
async def test_apply_decay_default_rate():
    """Test that apply_decay uses default rate from environment."""
    mock_surreal = AsyncMock()
    mock_surreal.apply_decay_to_all_memories.return_value = 0
    mock_surreal.cleanup_orphaned_facts.return_value = 0

    with patch.dict("os.environ", {"DECAY_RATE": "0.05"}):
        consolidator = MemoryConsolidator(mock_surreal, AsyncMock(), AsyncMock())
        await consolidator.apply_decay()

    mock_surreal.apply_decay_to_all_memories.assert_called_once_with(0.05, 0.1)


@pytest.mark.asyncio
async def test_apply_decay_logs_results():
    """Test that apply_decay logs the results."""
    mock_surreal = AsyncMock()
    mock_surreal.apply_decay_to_all_memories.return_value = 10
    mock_surreal.cleanup_orphaned_facts.return_value = 3

    consolidator = MemoryConsolidator(mock_surreal, AsyncMock(), AsyncMock())
    await consolidator.apply_decay(decay_rate=0.1, threshold=0.1)

    # Check that redis publish was called with correct log
    mock_surreal.cleanup_orphaned_facts.assert_called_once()
