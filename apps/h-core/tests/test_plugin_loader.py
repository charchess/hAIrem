import os
import yaml
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.infrastructure.plugin_loader import AgentRegistry, PluginLoader


def make_loader(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(exist_ok=True)
    registry = AgentRegistry()
    redis = MagicMock()
    redis.publish = AsyncMock()
    redis.publish_event = AsyncMock()
    redis.subscribe = AsyncMock()
    llm = MagicMock()
    llm.cache = None
    llm.get_completion = AsyncMock(return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]))
    llm.get_usage_from_response = MagicMock(return_value={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
    llm.get_model_provider = MagicMock(return_value=("test", "model"))
    return PluginLoader(str(agents_dir), registry, redis, llm), registry, agents_dir


@pytest.mark.asyncio
async def test_plugin_loader_load_valid_yaml(tmp_path):
    # Setup
    registry = AgentRegistry()
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    lisa_dir = agents_dir / "lisa"
    lisa_dir.mkdir()

    manifest_file = lisa_dir / "manifest.yaml"
    valid_data = {"name": "Lisa", "role": "Coordinator", "version": "1.0.0", "capabilities": ["chat", "orchestration"]}
    manifest_file.write_text(yaml.dump(valid_data))

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

    manifest_file = bad_dir / "manifest.yaml"
    manifest_file.write_text("invalid: [yaml: structure")  # Missing bracket

    mock_redis = MagicMock()
    mock_redis.subscribe = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_llm = MagicMock()
    loader = PluginLoader(str(agents_dir), registry, mock_redis, mock_llm)

    # Test (should not crash)
    await loader._initial_scan()

    # Assert
    assert len(registry.agents) == 0


class TestAgentRegistryExtra:
    def test_add_multiple_agents(self):
        registry = AgentRegistry()
        for name in ["lisa", "electra", "renarde"]:
            agent = MagicMock()
            agent.config.name = name
            registry.add_agent(agent)
        assert len(registry.agents) == 3


class TestPluginLoaderExtra:
    @pytest.mark.asyncio
    async def test_initial_scan_missing_directory(self, tmp_path):
        loader, registry, _ = make_loader(tmp_path)
        loader.agents_dir = str(tmp_path / "nonexistent")
        await loader._initial_scan()
        assert len(registry.agents) == 0

    @pytest.mark.asyncio
    async def test_load_agent_missing_name_skips(self, tmp_path):
        loader, registry, agents_dir = make_loader(tmp_path)
        agent_dir = agents_dir / "unnamed"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text(yaml.dump({"role": "assistant"}))
        await loader._load_agent(str(agent_dir / "manifest.yaml"))
        assert len(registry.agents) == 0

    @pytest.mark.asyncio
    async def test_load_agent_with_persona_yaml_merged(self, tmp_path):
        loader, registry, agents_dir = make_loader(tmp_path)
        agent_dir = agents_dir / "lisa"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text(yaml.dump({"name": "lisa", "role": "assistant"}))
        (agent_dir / "persona.yaml").write_text(yaml.dump({"description": "Warm AI"}))
        await loader._load_agent(str(agent_dir / "manifest.yaml"))
        assert "lisa" in registry.agents
        assert registry.agents["lisa"].config.description == "Warm AI"

    @pytest.mark.asyncio
    async def test_load_agent_system_prompt_renamed_to_prompt(self, tmp_path):
        loader, registry, agents_dir = make_loader(tmp_path)
        agent_dir = agents_dir / "electra"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text(
            yaml.dump({"name": "electra", "role": "assistant", "system_prompt": "You are Electra."})
        )
        await loader._load_agent(str(agent_dir / "manifest.yaml"))
        assert registry.agents["electra"].config.prompt == "You are Electra."

    @pytest.mark.asyncio
    async def test_load_agent_id_used_as_name(self, tmp_path):
        loader, registry, agents_dir = make_loader(tmp_path)
        agent_dir = agents_dir / "dieu"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text(yaml.dump({"id": "dieu", "role": "system"}))
        await loader._load_agent(str(agent_dir / "manifest.yaml"))
        assert "dieu" in registry.agents

    @pytest.mark.asyncio
    async def test_load_agent_handles_missing_manifest_exception(self, tmp_path):
        loader, registry, _ = make_loader(tmp_path)
        await loader._load_agent("/nonexistent/path/manifest.yaml")
        assert len(registry.agents) == 0

    @pytest.mark.asyncio
    async def test_load_agent_from_folder_success(self, tmp_path):
        loader, registry, agents_dir = make_loader(tmp_path)
        agent_dir = agents_dir / "renarde"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text(yaml.dump({"name": "renarde", "role": "trickster"}))
        result = await loader.load_agent_from_folder(str(agent_dir))
        assert result is True
        assert "renarde" in registry.agents

    @pytest.mark.asyncio
    async def test_load_agent_from_folder_no_manifest_returns_false(self, tmp_path):
        loader, registry, agents_dir = make_loader(tmp_path)
        agent_dir = agents_dir / "ghost"
        agent_dir.mkdir()
        result = await loader.load_agent_from_folder(str(agent_dir))
        assert result is False

    @pytest.mark.asyncio
    async def test_create_agent_folder_writes_manifest(self, tmp_path):
        loader, _, agents_dir = make_loader(tmp_path)
        folder = await loader.create_agent_folder({"name": "new_agent", "role": "test"})
        assert folder is not None
        assert os.path.exists(os.path.join(folder, "manifest.yaml"))

    @pytest.mark.asyncio
    async def test_create_agent_folder_no_name_returns_none(self, tmp_path):
        loader, _, _ = make_loader(tmp_path)
        folder = await loader.create_agent_folder({"role": "test"})
        assert folder is None

    def test_stop_when_observer_not_alive(self, tmp_path):
        loader, _, _ = make_loader(tmp_path)
        loader.stop()

    @pytest.mark.asyncio
    async def test_load_agent_with_custom_llm_config(self, tmp_path):
        loader, registry, agents_dir = make_loader(tmp_path)
        agent_dir = agents_dir / "custom"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text(
            yaml.dump(
                {"name": "custom", "role": "assistant", "llm_config": {"model": "custom/model", "api_key": "sk-test"}}
            )
        )
        await loader._load_agent(str(agent_dir / "manifest.yaml"))
        assert "custom" in registry.agents

    @pytest.mark.asyncio
    async def test_load_agent_replaces_existing_agent(self, tmp_path):
        loader, registry, agents_dir = make_loader(tmp_path)
        agent_dir = agents_dir / "lisa"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text(yaml.dump({"name": "lisa", "role": "assistant"}))

        await loader._load_agent(str(agent_dir / "manifest.yaml"))
        first_instance = registry.agents.get("lisa")

        await loader._load_agent(str(agent_dir / "manifest.yaml"))
        second_instance = registry.agents.get("lisa")

        assert first_instance is not second_instance
