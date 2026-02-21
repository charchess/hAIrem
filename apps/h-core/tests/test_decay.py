import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock
from src.infrastructure.surrealdb import SurrealDbClient
from src.domain.memory import MemoryConsolidator


@pytest.fixture
def mock_surreal():
    with patch("src.infrastructure.surrealdb.Surreal") as mock:
        yield mock


@pytest.mark.asyncio
async def test_apply_decay_calls_query(mock_surreal):
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()
    client._call = AsyncMock()

    # We want to test that apply_decay_to_all_memories sends the correct queries
    await client.apply_decay_to_all_memories(decay_rate=0.05, threshold=0.1)

    assert client._call.call_count == 2
    calls = client._call.call_args_list
    # Check for UPDATE BELIEVES - check for keywords to handle multi-line SQL
    query0 = str(calls[0]).replace("\n", " ").replace("  ", " ")
    assert "UPDATE BELIEVES" in query0
    assert "strength = strength * math::pow" in query0
    # Check for DELETE BELIEVES
    query1 = str(calls[1])
    assert "DELETE BELIEVES WHERE strength < 0.1" in query1


@pytest.mark.asyncio
async def test_memory_consolidator_decay_trigger():
    mock_surreal = AsyncMock()
    mock_llm = AsyncMock()
    mock_redis = AsyncMock()

    consolidator = MemoryConsolidator(mock_surreal, mock_llm, mock_redis)

    with patch.dict(os.environ, {"DECAY_RATE": "0.01"}):
        await consolidator.apply_decay(threshold=0.2)

    mock_surreal.apply_decay_to_all_memories.assert_called_once_with(0.01, 0.2)


@pytest.mark.asyncio
async def test_update_memory_strength_formatting(mock_surreal):
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()
    client._call = AsyncMock()

    await client.update_memory_strength("Lisa", "fact:123", boost=True)

    # Verify the formatting of subject:`lisa`
    call_args = client._call.call_args_list[0]
    query = call_args[0][1]
    assert "subject:`lisa`" in query
    assert "strength = math::min(1.0, strength + 0.1)" in query
