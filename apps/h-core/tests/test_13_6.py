import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.infrastructure.surrealdb import SurrealDbClient
from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig


@pytest.fixture
def mock_surreal():
    with patch("src.infrastructure.surrealdb.Surreal") as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield mock


@pytest.mark.asyncio
async def test_update_agent_state_logic():
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()
    client._call = AsyncMock()

    agent_id = "Lisa"
    relation_type = "WEARS"
    target_data = {"name": "red_dress", "description": "A beautiful red dress"}

    await client.update_agent_state(agent_id, relation_type, target_data)

    # 1. Check Update/Create node
    # 2. Check Relate

    assert client._call.call_count >= 2

    calls = [call[0][1] for call in client._call.call_args_list]

    # Verify Target Node Update
    assert any("INSERT INTO subject" in c for c in calls)

    # Verify New Relation
    assert any("RELATE subject:`lisa`->WEARS->subject:`red_dress`" in c for c in calls)


@pytest.mark.asyncio
async def test_get_agent_state_query():
    client = SurrealDbClient("ws://localhost:8000", "root", "root")
    client.client = MagicMock()
    client._call = AsyncMock()

    await client.get_agent_state("Lisa")

    query = client._call.call_args[0][1]
    # Check for generic graph traversal
    assert "FROM subject:`lisa`" in query


@pytest.mark.asyncio
async def test_recall_memory_includes_live_facts():
    config = AgentConfig(name="Lisa", role="Muse")
    redis = AsyncMock()
    llm = AsyncMock()
    surreal = AsyncMock()

    agent = BaseAgent(config, redis, llm, surreal)

    # Mock live facts
    surreal.get_agent_state.return_value = [
        {"relation": "WEARS", "name": "red_dress", "description": "A beautiful red dress"},
        {"relation": "IS_IN", "name": "bedroom", "description": "Lisas bedroom"},
    ]

    llm.get_embedding.return_value = [0.1] * 768
    surreal.semantic_search.return_value = []

    result = await agent.recall_memory("What am I wearing?")

    assert "### LIVE FACTS (OBJECTIVE REALITY) ###" in result
    assert "CURRENTLY WEARS: A beautiful red dress" in result
    assert "CURRENTLY IS IN: Lisas bedroom" in result
    assert "No relevant past memories found." in result


@pytest.mark.asyncio
async def test_agent_skills_initiation():
    config = AgentConfig(name="Lisa", role="Muse")
    redis = AsyncMock()
    llm = AsyncMock()
    surreal = AsyncMock()
    visual = AsyncMock()

    agent = BaseAgent(config, redis, llm, surreal, visual)

    # Test move_to skill
    res_move = await agent.move_to("the beach")
    assert "Success" in res_move
    surreal.update_agent_state.assert_any_call("Lisa", "IS_IN", {"name": "the beach", "description": "The the beach"})

    # Test change_outfit skill
    res_outfit = await agent.change_outfit("a yellow bikini")
    assert "Success" in res_outfit
    from unittest.mock import ANY

    surreal.update_agent_state.assert_any_call("Lisa", "WEARS", ANY)

    # Verify visual was triggered
    visual.generate_and_index.assert_called_once()
    args = visual.generate_and_index.call_args[1]
    assert args["agent_id"] == "Lisa"
    assert "yellow bikini" in args["prompt"]
