import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.infrastructure.surrealdb import SurrealDbClient
from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig

@pytest.fixture
def mock_surreal():
    with patch("src.infrastructure.surrealdb.Surreal") as mock:
        yield mock

@pytest.mark.asyncio
async def test_subjective_semantic_search_query(mock_surreal):
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()
    client._call = AsyncMock()
    
    embedding = [0.1] * 768
    await client.semantic_search(embedding, agent_id="Lisa")
    
    assert client._call.call_count == 1
    query = client._call.call_args[0][1]
    assert "subject:`lisa`" in query
    assert "subject:`system`" in query
    assert "<-BELIEVES" in query

@pytest.mark.asyncio
async def test_agent_recall_memory_passes_id():
    config = AgentConfig(name="Electra", role="Technician")
    redis = AsyncMock()
    llm = AsyncMock()
    surreal = AsyncMock()
    
    agent = BaseAgent(config, redis, llm, surreal)
    
    llm.get_embedding.return_return = [0.1] * 768
    surreal.semantic_search.return_value = []
    
    await agent.recall_memory("anything")
    
    # Check that Electra passed her name
    surreal.semantic_search.assert_called_once()
    args, kwargs = surreal.semantic_search.call_args
    assert kwargs.get('agent_id') == "Electra"
