import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.models.agent import AgentConfig
from src.domain.agent import BaseAgent


def _make_agent():
    config = AgentConfig(
        name="Electra",
        role="Experte domotique",
        system_prompt="Tu es Electra.",
        capabilities=["home_automation", "shopping"],
    )
    redis = MagicMock()
    redis.publish = AsyncMock()
    llm = MagicMock()
    llm.model = "gpt-4"
    llm.chat = AsyncMock(return_value="HA command executed.")

    with patch("electra.logic.HaClient") as MockHaClient:
        mock_ha = MagicMock()
        mock_ha.call_service = AsyncMock(return_value=True)
        mock_ha.get_state = AsyncMock(return_value={"state": "on"})
        mock_ha.fetch_all_states = AsyncMock(return_value=[])
        mock_ha.close = AsyncMock()
        MockHaClient.return_value = mock_ha

        from electra.logic import Agent

        agent = Agent(
            config=config,
            redis_client=redis,
            llm_client=llm,
            surreal_client=None,
            visual_service=None,
            agent_registry=None,
        )
        agent._mock_ha = mock_ha
        return agent


def test_electra_tools_registered_at_setup():
    agent = _make_agent()
    assert "get_entity_state" in agent.tools
    assert "call_ha_service" in agent.tools
    assert "run_routine" in agent.tools
    assert "manage_shopping_list" in agent.tools


def test_electra_preserves_default_tools():
    agent = _make_agent()
    assert "send_internal_note" in agent.tools


@pytest.mark.asyncio
async def test_get_entity_state_returns_state():
    agent = _make_agent()
    state = await agent.get_entity_state("light.kitchen")
    assert state == "on"


@pytest.mark.asyncio
async def test_call_ha_service_calls_ha_client():
    agent = _make_agent()
    result = await agent.call_ha_service("light.turn_on", "light.kitchen")
    assert result == "Done"
    agent._mock_ha.call_service.assert_called_once()


@pytest.mark.asyncio
async def test_manage_shopping_list_add():
    agent = _make_agent()
    result = await agent.manage_shopping_list("add", "Coffee")
    assert "Coffee" in result


@pytest.mark.asyncio
async def test_manage_shopping_list_list():
    agent = _make_agent()
    result = await agent.manage_shopping_list("list")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_run_routine_unknown_returns_error():
    agent = _make_agent()
    result = await agent.run_routine("non_existent_routine")
    assert "not found" in result.lower() or "error" in result.lower()


@pytest.mark.asyncio
async def test_run_routine_movie_mode():
    agent = _make_agent()
    result = await agent.run_routine("movie_mode")
    assert "movie_mode" in result
