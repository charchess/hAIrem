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


class TestValidateParameters:
    def test_validate_parameters_valid_temperature(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"temperature": 1.0})
        assert len(errors) == 0
    
    def test_validate_parameters_invalid_temperature_high(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"temperature": 2.5})
        assert len(errors) == 1
        assert errors[0].field == "temperature"
        assert "2.0" in errors[0].message
    
    def test_validate_parameters_invalid_temperature_low(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"temperature": -0.5})
        assert len(errors) == 1
        assert errors[0].field == "temperature"
    
    def test_validate_parameters_valid_max_tokens(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"max_tokens": 4096})
        assert len(errors) == 0
    
    def test_validate_parameters_invalid_max_tokens(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"max_tokens": 10000})
        assert len(errors) == 1
        assert errors[0].field == "max_tokens"
    
    def test_validate_parameters_valid_top_p(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"top_p": 0.9})
        assert len(errors) == 0
    
    def test_validate_parameters_invalid_top_p(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"top_p": 1.5})
        assert len(errors) == 1
        assert errors[0].field == "top_p"
    
    def test_validate_parameters_invalid_top_k(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"top_k": 0})
        assert len(errors) == 1
        assert errors[0].field == "top_k"
    
    def test_validate_parameters_valid_presence_penalty(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"presence_penalty": 1.0})
        assert len(errors) == 0
    
    def test_validate_parameters_invalid_presence_penalty(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"presence_penalty": 3.0})
        assert len(errors) == 1
        assert errors[0].field == "presence_penalty"
    
    def test_validate_parameters_valid_context_window(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"context_window": 32000})
        assert len(errors) == 0
    
    def test_validate_parameters_invalid_context_window(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"context_window": 500})
        assert len(errors) == 1
        assert errors[0].field == "context_window"
    
    def test_validate_parameters_valid_base_url_https(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"base_url": "https://api.openai.com"})
        assert len(errors) == 0
    
    def test_validate_parameters_valid_base_url_http(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"base_url": "http://localhost:11434"})
        assert len(errors) == 0
    
    def test_validate_parameters_invalid_base_url(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"base_url": "api.openai.com"})
        assert len(errors) == 1
        assert errors[0].field == "base_url"
    
    def test_validate_parameters_invalid_model_whitespace(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"model": "   "})
        assert len(errors) == 1
        assert errors[0].field == "model"
    
    def test_validate_parameters_valid_model(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({"model": "gpt-4o"})
        assert len(errors) == 0
    
    def test_validate_parameters_multiple_errors(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({
            "temperature": 3.0,
            "max_tokens": 0,
            "top_p": 1.5,
            "base_url": "invalid"
        })
        assert len(errors) == 4
    
    def test_validate_parameters_none_values_ignored(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        errors = service.validate_parameters({
            "temperature": None,
            "max_tokens": None,
            "top_p": None
        })
        assert len(errors) == 0


class TestSaveConfig:
    @pytest.mark.asyncio
    async def test_save_config_empty_agent_id(self):
        from src.features.admin.agent_config.service import AgentConfigService
        service = AgentConfigService(surreal_client=MagicMock())
        
        result = await service.save_config("", {"temperature": 1.0})
        
        assert result["success"] is False
        assert any(e["field"] == "agent_id" for e in result["errors"])
    
    @pytest.mark.asyncio
    async def test_save_config_invalid_parameters(self):
        from src.features.admin.agent_config.service import AgentConfigService
        mock_surreal = MagicMock()
        mock_surreal._call = AsyncMock()
        service = AgentConfigService(surreal_client=mock_surreal)
        
        result = await service.save_config("agent1", {"temperature": 5.0})
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_save_config_success(self):
        from src.features.admin.agent_config.service import AgentConfigService
        mock_surreal = MagicMock()
        mock_surreal._call = AsyncMock(return_value=[{"result": []}])
        service = AgentConfigService(surreal_client=mock_surreal)
        
        result = await service.save_config("agent1", {"temperature": 1.0, "model": "gpt-4o"})
        
        assert result["success"] is True
        assert result["agent_id"] == "agent1"
        assert result["parameters"]["temperature"] == 1.0
        assert "agent1" in service._config_cache
    
    @pytest.mark.asyncio
    async def test_save_config_updates_cache(self):
        from src.features.admin.agent_config.service import AgentConfigService
        mock_surreal = MagicMock()
        mock_surreal._call = AsyncMock(return_value=[{"result": []}])
        service = AgentConfigService(surreal_client=mock_surreal)
        
        await service.save_config("agent1", {"temperature": 0.5})
        
        assert service._config_cache["agent1"].temperature == 0.5
        
        await service.save_config("agent1", {"temperature": 0.9})
        
        assert service._config_cache["agent1"].temperature == 0.9


class TestGetConfig:
    @pytest.mark.asyncio
    async def test_get_config_from_cache(self):
        from src.features.admin.agent_config.service import AgentConfigService
        from src.features.admin.agent_config.models import AgentParameters
        mock_surreal = MagicMock()
        service = AgentConfigService(surreal_client=mock_surreal)
        service._config_cache["agent1"] = AgentParameters(temperature=0.8, model="gpt-4o")
        
        result = await service.get_config("agent1")
        
        assert result["success"] is True
        assert result["agent_id"] == "agent1"
        assert result["parameters"]["temperature"] == 0.8
    
    @pytest.mark.asyncio
    async def test_get_config_from_repository(self):
        from src.features.admin.agent_config.service import AgentConfigService
        from src.features.admin.agent_config.models import AgentParameters, AgentConfigSchema
        mock_surreal = MagicMock()
        mock_surreal._call = AsyncMock(return_value=[{
            "result": [{
                "agent_id": "agent1",
                "parameters": {"temperature": 0.7},
                "enabled": True,
                "version": "1.0.0"
            }]
        }])
        service = AgentConfigService(surreal_client=mock_surreal)
        
        result = await service.get_config("agent1")
        
        assert result["success"] is True
        assert result["agent_id"] == "agent1"
        assert result["parameters"]["temperature"] == 0.7
        assert "agent1" in service._config_cache


class TestPersistence:
    @pytest.mark.asyncio
    async def test_repository_save_creates_config(self):
        from src.features.admin.agent_config.repository import AgentConfigRepository
        from src.features.admin.agent_config.models import AgentParameters
        mock_surreal = MagicMock()
        mock_surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = AgentConfigRepository(mock_surreal)
        
        params = AgentParameters(temperature=0.9, model="gpt-4o-mini")
        result = await repo.save("test_agent", params)
        
        assert result.agent_id == "test_agent"
        assert result.parameters.temperature == 0.9
        mock_surreal._call.assert_called()
    
    @pytest.mark.asyncio
    async def test_repository_get_returns_config(self):
        from src.features.admin.agent_config.repository import AgentConfigRepository
        mock_surreal = MagicMock()
        mock_surreal._call = AsyncMock(return_value=[{
            "result": [{
                "agent_id": "agent1",
                "parameters": {"temperature": 0.5, "model": "ollama/mistral"},
                "enabled": True,
                "version": "1.0.0"
            }]
        }])
        repo = AgentConfigRepository(mock_surreal)
        
        result = await repo.get("agent1")
        
        assert result is not None
        assert result.agent_id == "agent1"
        assert result.parameters.temperature == 0.5
    
    @pytest.mark.asyncio
    async def test_repository_get_returns_none_when_not_found(self):
        from src.features.admin.agent_config.repository import AgentConfigRepository
        mock_surreal = MagicMock()
        mock_surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = AgentConfigRepository(mock_surreal)
        
        result = await repo.get("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_repository_delete_removes_config(self):
        from src.features.admin.agent_config.repository import AgentConfigRepository
        mock_surreal = MagicMock()
        mock_surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = AgentConfigRepository(mock_surreal)
        
        result = await repo.delete("agent1")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_repository_list_all_returns_all_configs(self):
        from src.features.admin.agent_config.repository import AgentConfigRepository
        mock_surreal = MagicMock()
        mock_surreal._call = AsyncMock(return_value=[{
            "result": [
                {"agent_id": "agent1", "parameters": {"temperature": 0.5}, "enabled": True, "version": "1.0.0"},
                {"agent_id": "agent2", "parameters": {"temperature": 0.7}, "enabled": True, "version": "1.0.0"}
            ]
        }])
        repo = AgentConfigRepository(mock_surreal)
        
        result = await repo.list_all()
        
        assert len(result) == 2
        assert result[0].agent_id == "agent1"
        assert result[1].agent_id == "agent2"
    
    @pytest.mark.asyncio
    async def test_repository_get_or_default_returns_default_when_not_found(self):
        from src.features.admin.agent_config.repository import AgentConfigRepository
        from src.features.admin.agent_config.models import DEFAULT_PARAMETERS
        mock_surreal = MagicMock()
        mock_surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = AgentConfigRepository(mock_surreal)
        
        result = await repo.get_or_default("nonexistent")
        
        assert result.temperature == DEFAULT_PARAMETERS.temperature
        assert result.max_tokens == DEFAULT_PARAMETERS.max_tokens
