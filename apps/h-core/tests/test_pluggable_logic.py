import os
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.infrastructure.plugin_loader import AgentRegistry, PluginLoader

@pytest.mark.asyncio
async def test_custom_logic_loading():
    # Setup
    registry = AgentRegistry()
    mock_redis = MagicMock()
    mock_redis.subscribe = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_llm = MagicMock()
    mock_llm.cache = None
    
    # Path to our dummy agent
    agents_dir = os.path.join(os.path.dirname(__file__), "dummy_agent")
    # We need to point to the parent of dummy_agent since walking starts from agents_dir
    parent_dir = os.path.dirname(agents_dir)
    
    loader = PluginLoader(parent_dir, registry, mock_redis, mock_llm)
    
    # Test
    await loader._initial_scan()
    
    # Assert
    assert "Dummy" in registry.agents
    agent = registry.agents["Dummy"]
    
    # Verify it's our custom class
    from src.domain.agent import BaseAgent
    assert isinstance(agent, BaseAgent)
    assert agent.__class__.__name__ == "Agent" # Class name from logic.py
    
    # Verify the custom command is registered
    assert "hello_dummy" in agent.command_handlers
    
    # Test the command
    result = await agent.command_handlers["hello_dummy"]({})
    assert result == "Hello from Dummy Agent"
