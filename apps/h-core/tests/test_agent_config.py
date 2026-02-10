import os
import yaml
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.infrastructure.plugin_loader import AgentRegistry, PluginLoader
from src.models.agent import AgentConfig

@pytest.mark.asyncio
async def test_per_agent_llm_config_loading(tmp_path):
    # Setup
    registry = AgentRegistry()
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    
    lisa_dir = agents_dir / "lisa"
    lisa_dir.mkdir()
    
    manifest_file = lisa_dir / "manifest.yaml"
    valid_data = {
        "name": "Lisa",
        "role": "Coordinator",
        "version": "1.0.0",
        "llm_config": {
            "model": "gpt-4o-mini",
            "temperature": 0.2
        }
    }
    manifest_file.write_text(yaml.dump(valid_data))
    
    # Mock infrastructure clients
    mock_redis = MagicMock()
    mock_redis.subscribe = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_llm = MagicMock()
    mock_llm.cache = None
    mock_surreal = MagicMock()
    
    loader = PluginLoader(str(agents_dir), registry, mock_redis, mock_llm, mock_surreal)
    
    # Test
    await loader._initial_scan()
    
    # Assert
    assert "Lisa" in registry.agents
    agent = registry.agents["Lisa"]
    # Verify that agent has its own LlmClient with overridden values
    assert agent.llm.model == "gpt-4o-mini"
    assert agent.llm.temperature == 0.2
    # Verify it's a different instance than the global mock_llm
    assert agent.llm != mock_llm

@pytest.mark.asyncio
async def test_agent_config_no_override(tmp_path):
    # Setup
    registry = AgentRegistry()
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    
    manifest_file = agents_dir / "standard" / "manifest.yaml"
    manifest_file.parent.mkdir()
    valid_data = {
        "name": "StandardAgent",
        "role": "Assistant",
    }
    manifest_file.write_text(yaml.dump(valid_data))
    
    mock_redis = MagicMock()
    mock_redis.subscribe = AsyncMock()
    mock_redis.publish = AsyncMock()
    # Mock global LLM with a specific model
    mock_llm = MagicMock()
    mock_llm.model = "global-default-model"
    
    loader = PluginLoader(str(agents_dir), registry, mock_redis, mock_llm)
    
    # Test
    await loader._initial_scan()
    
    # Assert
    assert "StandardAgent" in registry.agents
    agent = registry.agents["StandardAgent"]
    # Should use the global llm instance
    assert agent.llm == mock_llm
    assert agent.llm.model == "global-default-model"
