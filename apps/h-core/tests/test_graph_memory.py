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
        None, # Upsert Subject
        None, # Upsert Agent
        [{"id": "fact:123"}], # Create Fact
        None, # Relate Agent -> BELIEVES -> Fact
        None  # Relate Fact -> ABOUT -> Subject
    ]
    
    fact_data = {
        "fact": "Lisa likes sushi",
        "subject": "Lisa",
        "agent": "Renarde",
        "confidence": 0.95,
        "embedding": [0.1, 0.2]
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
    
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", MagicMock()):
        await client.setup_schema()
        
    # Should call query at least twice (messages + graph_schema)
    assert client._call.call_count >= 2
