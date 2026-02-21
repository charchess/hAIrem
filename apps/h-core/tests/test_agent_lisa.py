import asyncio
import os
import sys

import pytest
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath("../../agents"))

from src.models.agent import AgentConfig
from lisa.logic import Agent


def _make_agent() -> Agent:
    config = AgentConfig(
        name="lisa",
        role="assistant",
        skills=[
            {"name": "get_fridge_status", "description": "desc"},
            {"name": "get_house_status", "description": "desc"},
            {"name": "add_reminder", "description": "desc"},
        ],
    )
    redis = MagicMock()
    redis.publish = AsyncMock()
    redis.publish_event = AsyncMock()
    llm = MagicMock()
    return Agent(config=config, redis_client=redis, llm_client=llm)


def test_lisa_tools_registered_at_setup():
    agent = _make_agent()
    assert "get_fridge_status" in agent.tools
    assert "get_house_status" in agent.tools
    assert "add_reminder" in agent.tools


def test_get_house_status_returns_string():
    agent = _make_agent()
    result = asyncio.run(agent.get_house_status())
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_fridge_status_returns_string():
    agent = _make_agent()
    result = asyncio.run(agent.get_fridge_status())
    assert isinstance(result, str)
    assert len(result) > 0


def test_add_reminder_stores_data():
    agent = _make_agent()
    result = asyncio.run(agent.add_reminder("Acheter du lait"))
    assert "Acheter du lait" in result
