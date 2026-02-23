import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.skills.registry import SkillRegistry


def test_skill_registry_loads_home_assistant_tools():
    registry = SkillRegistry()
    tools = registry.load("home_assistant")
    assert isinstance(tools, dict)
    assert len(tools) > 0
    assert "turn_on" in tools
    assert "turn_off" in tools
    assert "get_state" in tools


def test_skill_registry_returns_callable_functions():
    registry = SkillRegistry()
    tools = registry.load("home_assistant")
    for name, fn in tools.items():
        assert callable(fn), f"Tool '{name}' must be callable"


def test_skill_registry_loads_weather_tools():
    registry = SkillRegistry()
    tools = registry.load("weather")
    assert isinstance(tools, dict)
    assert len(tools) > 0


def test_skill_registry_loads_calendar_tools():
    registry = SkillRegistry()
    tools = registry.load("calendar")
    assert isinstance(tools, dict)
    assert len(tools) > 0


def test_skill_registry_raises_on_unknown_skill():
    registry = SkillRegistry()
    with pytest.raises(ValueError, match="unknown_skill_xyz"):
        registry.load("unknown_skill_xyz")


def test_skill_registry_list_available():
    registry = SkillRegistry()
    available = registry.list_available()
    assert "home_assistant" in available
    assert "weather" in available
    assert "calendar" in available
    assert "cooking" in available


def test_agent_registers_skill_tools_from_package():
    from unittest.mock import MagicMock
    from src.domain.agent import BaseAgent
    from src.models.agent import AgentConfig

    config = AgentConfig(
        name="test_agent",
        role="test",
        skills=[
            {"name": "turn_on", "description": "Turn on a HA entity"},
            {"name": "get_state", "description": "Get HA entity state"},
        ],
    )
    redis_mock = MagicMock()
    llm_mock = MagicMock()
    llm_mock.cache = None

    agent = BaseAgent(config=config, redis_client=redis_mock, llm_client=llm_mock)

    assert "turn_on" in agent.tools
    assert "get_state" in agent.tools
    assert callable(agent.tools["turn_on"]["function"])
    assert callable(agent.tools["get_state"]["function"])
