import yaml
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.infrastructure.plugin_loader import AgentRegistry, PluginLoader

@pytest.mark.asyncio
async def test_plugin_loader_load_valid_yaml(tmp_path):
    # Setup
    registry = AgentRegistry()
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    
    lisa_dir = agents_dir / "lisa"
    lisa_dir.mkdir()
    
    expert_file = lisa_dir / "expert.yaml"
    valid_data = {
        "name": "Lisa",
        "role": "Coordinator",
        "version": "1.0.0",
        "capabilities": ["chat", "orchestration"]
    }
    expert_file.write_text(yaml.dump(valid_data))
    
    mock_redis = MagicMock()
    mock_redis.subscribe = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_llm = MagicMock()
    mock_llm.cache = None
    loader = PluginLoader(str(agents_dir), registry, mock_redis, mock_llm)
    
    # Test
    await loader._initial_scan()
    
    # Assert
    assert "Lisa" in registry.agents
    assert registry.agents["Lisa"].config.role == "Coordinator"

@pytest.mark.asyncio
async def test_plugin_loader_invalid_yaml(tmp_path):
    # Setup
    registry = AgentRegistry()
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    
    bad_dir = agents_dir / "broken"
    bad_dir.mkdir()
    
    expert_file = bad_dir / "expert.yaml"
    expert_file.write_text("invalid: [yaml: structure") # Missing bracket
    
    mock_redis = MagicMock()
    mock_redis.subscribe = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_llm = MagicMock()
    loader = PluginLoader(str(agents_dir), registry, mock_redis, mock_llm)
    
    # Test (should not crash)
    await loader._initial_scan()
    
    # Assert
    assert len(registry.agents) == 0
