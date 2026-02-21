import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from src.domain.memory import MemoryConsolidator, ConflictResolver


@pytest.mark.asyncio
async def test_conflict_resolver_logic():
    mock_llm = AsyncMock()
    resolver = ConflictResolver(mock_llm)

    # Mock LLM response for conflict
    mock_llm.get_completion.return_value = json.dumps(
        {"is_conflict": True, "resolution": "User no longer likes tea", "action": "OVERRIDE"}
    )

    res = await resolver.resolve("User likes tea", "User hates tea")
    assert res["is_conflict"] is True
    assert res["action"] == "OVERRIDE"


@pytest.mark.asyncio
async def test_consolidator_triggers_conflict_check():
    mock_surreal = AsyncMock()
    mock_llm = AsyncMock()
    mock_redis = AsyncMock()

    consolidator = MemoryConsolidator(mock_surreal, mock_llm, mock_redis)

    # 1. Mock unprocessed messages
    mock_surreal.get_unprocessed_messages.return_value = [
        {"id": "msg:1", "sender": {"agent_id": "user"}, "payload": {"content": "I hate tea now"}}
    ]

    # 2. Mock LLM fact extraction
    mock_llm.get_completion.side_effect = [
        json.dumps(
            {
                "facts": [{"fact": "User hates tea", "subject": "user", "confidence": 1.0}],
                "causal_links": [],
                "concepts": [],
            }
        ),  # Extraction
        json.dumps(
            {"is_conflict": True, "resolution": "User changed mind about tea", "action": "OVERRIDE"}
        ),  # Resolution
    ]
    mock_llm.get_embedding.return_value = [0.1] * 768

    # 3. Mock semantic search returning a match
    mock_surreal.semantic_search.return_value = [{"id": "fact:old", "content": "User likes tea", "score": 0.9}]

    await consolidator.consolidate()

    # Verify merge_or_override was called instead of insert_graph_memory
    mock_surreal.merge_or_override_fact.assert_called_once()
    mock_surreal.insert_graph_memory.assert_not_called()
