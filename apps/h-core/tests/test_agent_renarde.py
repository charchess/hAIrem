import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../agents")))

import pytest
from unittest.mock import MagicMock, AsyncMock
from src.models.agent import AgentConfig
from src.domain.agent import BaseAgent
from renarde.logic import Agent


def _make_agent():
    config = AgentConfig(
        name="renarde",
        role="coordinator",
        description="Le visage de hAIrem",
    )
    mock_redis = MagicMock()
    mock_redis.subscribe = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_redis.publish_event = AsyncMock()
    mock_llm = MagicMock()
    mock_llm.cache = None
    return Agent(config=config, redis_client=mock_redis, llm_client=mock_llm)


def test_renarde_tools_registered_at_setup():
    agent = _make_agent()
    assert "greet_user" in agent.tools
    assert "get_crew_status" in agent.tools
    assert "suggest_topic" in agent.tools


@pytest.mark.asyncio
async def test_greet_user_returns_welcoming_message():
    agent = _make_agent()
    result = await agent.greet_user(user_name="Alice")
    assert isinstance(result, str)
    assert "Alice" in result


@pytest.mark.asyncio
async def test_suggest_topic_returns_non_empty_string():
    agent = _make_agent()
    result = await agent.suggest_topic()
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_get_crew_status_returns_string():
    agent = _make_agent()
    result = await agent.get_crew_status()
    assert isinstance(result, str)
    assert len(result) > 0
