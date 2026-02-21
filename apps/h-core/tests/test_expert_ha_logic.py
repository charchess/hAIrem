import os
import pytest
import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Robust root detection
current_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_dir, "../../../"))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.infrastructure.plugin_loader import AgentRegistry, PluginLoader


@pytest.mark.asyncio
async def test_expert_domotique_logic_loading():
    # Setup
    registry = AgentRegistry()
    mock_redis = MagicMock()
    mock_redis.subscribe = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_redis.publish_event = AsyncMock()
    mock_llm = MagicMock()
    mock_llm.cache = None

    # Path to actual expert-domotique
    agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../agents"))

    loader = PluginLoader(agents_dir, registry, mock_redis, mock_llm)

    # Test loading
    await loader._initial_scan()

    # Assert
    assert "Electra" in registry.agents
    agent = registry.agents["Electra"]

    # Verify it's the custom Agent class
    assert agent.__class__.__name__ == "Agent"
    assert hasattr(agent, "ha")

    # Verify tools are registered
    tool_names = [t["function"]["name"] for t in agent.get_tools_schema()]
    assert "get_entity_state" in tool_names
    assert "call_ha_service" in tool_names


@pytest.mark.asyncio
async def test_expert_ha_tools_execution():
    # Robust root detection
    import sys
    import os
    import importlib.util

    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.abspath(os.path.join(current_dir, "../../../"))
    if root_path not in sys.path:
        sys.path.insert(0, root_path)

    # Load logic.py directly
    logic_path = os.path.join(root_path, "agents/electra/logic.py")
    spec = importlib.util.spec_from_file_location("electra_logic", logic_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    Agent = module.Agent

    # Setup agent with mocked HA
    mock_ha = MagicMock()
    mock_ha.get_state = AsyncMock(return_value={"state": "on", "attributes": {"unit_of_measurement": "%"}})
    mock_ha.call_service = AsyncMock(return_value=True)

    from src.models.agent import AgentConfig

    config = AgentConfig(name="Electra", role="Expert")
    agent = Agent(config=config, redis_client=MagicMock(), llm_client=MagicMock())
    agent.ha = mock_ha

    # Test get_entity_state
    result = await agent.get_entity_state("sensor.test")
    assert result == "on"
    mock_ha.get_state.assert_called_with("sensor.test")

    # Test call_ha_service
    result = await agent.call_ha_service("light.turn_on", "light.kitchen")
    assert "Done" in result
    mock_ha.call_service.assert_called()


@pytest.mark.asyncio
async def test_expert_ha_routines_execution():
    import os
    import importlib.util

    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.abspath(os.path.join(current_dir, "../../../"))
    logic_path = os.path.join(root_path, "agents/electra/logic.py")
    spec = importlib.util.spec_from_file_location("electra_logic_2", logic_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    Agent = module.Agent

    mock_ha = MagicMock()
    mock_ha.call_service = AsyncMock(return_value=True)

    from src.models.agent import AgentConfig

    config = AgentConfig(name="Electra", role="Expert")
    agent = Agent(config=config, redis_client=MagicMock(), llm_client=MagicMock())
    agent.ha = mock_ha

    # Test valid routine
    result = await agent.run_routine("movie_mode")
    assert "successfully" in result
    assert mock_ha.call_service.call_count == 2

    # Test invalid routine
    result_invalid = await agent.run_routine("invalid")
    assert "Error" in result_invalid
