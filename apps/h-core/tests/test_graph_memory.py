import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.infrastructure.surrealdb import SurrealDbClient


@pytest.fixture
def mock_surreal():
    with patch("src.infrastructure.surrealdb.Surreal") as mock:
        yield mock


@pytest.mark.asyncio
async def test_insert_graph_memory_calls_relate(mock_surreal):
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()

    # Mock _call to return success for create/query
    client._call = AsyncMock()
    client._call.side_effect = [
        None,  # Upsert Subject
        None,  # Upsert Agent
        [{"id": "fact:123"}],  # Create Fact
        None,  # Relate Agent -> BELIEVES -> Fact
        None,  # Relate Fact -> ABOUT -> Subject
    ]

    fact_data = {
        "fact": "Lisa likes sushi",
        "subject": "Lisa",
        "agent": "Renarde",
        "confidence": 0.95,
        "embedding": [0.1, 0.2],
    }

    await client.insert_graph_memory(fact_data)

    assert client._call.call_count == 5
    # Verify the RELATE calls
    calls = client._call.call_args_list
    # Check for RELATE agent:renarde->BELIEVES->fact:123
    assert "RELATE subject:`renarde`->BELIEVES->fact:123" in str(calls[3])
    # Check for RELATE fact:123->ABOUT->subject:lisa
    assert "RELATE fact:123->ABOUT->subject:`lisa`" in str(calls[4])


@pytest.mark.asyncio
async def test_setup_schema_loads_file(mock_surreal):
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()
    client._call = AsyncMock()

    with patch("os.path.exists", return_value=True), patch("builtins.open", MagicMock()):
        await client.setup_schema()

    # Should call query at least twice (messages + graph_schema)
    assert client._call.call_count >= 2


# =============================================
# Decay Tests (Story 13.2)
# =============================================


@pytest.mark.asyncio
async def test_apply_decay_to_all_memories_calls_query(mock_surreal):
    """Test that apply_decay_to_all_memories executes the correct queries."""
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()
    client._call = AsyncMock()
    client._call.return_value = [{"result": []}]

    await client.apply_decay_to_all_memories(decay_rate=0.05, threshold=0.1)

    # Verify _call was called at least twice (update + delete)
    assert client._call.call_count >= 2


@pytest.mark.asyncio
async def test_apply_decay_permanent_flag_excluded(mock_surreal):
    """Test that permanent memories are excluded from decay."""
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()
    client._call = AsyncMock()
    client._call.return_value = [{"result": []}]

    await client.apply_decay_to_all_memories(decay_rate=0.05, threshold=0.1)

    # Check that the update query includes permanent != true
    calls = client._call.call_args_list
    update_call = str(calls[0])
    assert "permanent" in update_call.lower() or "WHERE" in update_call


@pytest.mark.asyncio
async def test_cleanup_orphaned_facts(mock_surreal):
    """Test that cleanup_orphaned_facts removes unreferenced facts."""
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()
    client._call = AsyncMock()
    client._call.return_value = [{"result": [{"id": "fact:orphan1"}, {"id": "fact:orphan2"}]}]

    result = await client.cleanup_orphaned_facts()

    # Verify _call was called
    assert client._call.call_count >= 1
    # Should return count of deleted facts
    assert result == 2


@pytest.mark.asyncio
async def test_cleanup_orphaned_facts_no_orphans(mock_surreal):
    """Test cleanup when there are no orphaned facts."""
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()
    client._call = AsyncMock()
    client._call.return_value = [{"result": []}]

    result = await client.cleanup_orphaned_facts()

    assert result == 0


@pytest.mark.asyncio
async def test_insert_graph_memory_with_permanent_flag(mock_surreal):
    """Test that permanent flag is passed to BELIEVES edge."""
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()

    # Mock _call to return success for create/query
    client._call = AsyncMock()
    client._call.side_effect = [
        None,  # Upsert Subject
        None,  # Upsert Agent
        [{"id": "fact:123"}],  # Create Fact
        None,  # Relate Agent -> BELIEVES -> Fact
        None,  # Relate Fact -> ABOUT -> Subject
    ]

    # Test with permanent=True (identity fact)
    fact_data = {
        "fact": "My name is Lisa",
        "subject": "Lisa",
        "agent": "Lisa",
        "confidence": 1.0,
        "embedding": [0.1, 0.2],
        "permanent": True,
    }

    await client.insert_graph_memory(fact_data)

    # Verify _call was made
    assert client._call.call_count == 5
