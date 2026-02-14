import pytest
from unittest.mock import MagicMock, AsyncMock
from src.features.admin.agent_creation.models import AgentCreationPayload
from src.features.admin.agent_creation.service import AgentCreationService
from src.features.admin.agent_creation.repository import AgentCreationRepository


def create_mock_surreal():
    mock_surreal = MagicMock()
    mock_surreal._call = AsyncMock(return_value=[{"result": []}])
    return mock_surreal


def create_payload(name: str = "TestAgent", role: str = "Assistant", **kwargs) -> AgentCreationPayload:
    return AgentCreationPayload(
        name=name,
        role=role,
        description=kwargs.get("description", "Test description"),
        prompt=kwargs.get("prompt", "You are a helpful assistant"),
        model=kwargs.get("model", "ollama/mistral"),
        temperature=kwargs.get("temperature", 0.7),
        max_tokens=kwargs.get("max_tokens", 2048),
        top_p=kwargs.get("top_p", 0.9),
        enabled=kwargs.get("enabled", True),
        agents_folder=kwargs.get("agents_folder", None),
    )


@pytest.mark.asyncio
async def test_create_agent_success():
    mock_surreal = create_mock_surreal()
    service = AgentCreationService(surreal_client=mock_surreal)

    payload = create_payload("NewAgent")

    result = await service.create_agent(payload)

    assert result["success"] is True
    assert result["agent_id"] == "NewAgent"
    assert "created successfully" in result["message"]


@pytest.mark.asyncio
async def test_create_agent_already_exists():
    mock_surreal = MagicMock()
    mock_surreal._call = AsyncMock(return_value=[{
        "result": [{
            "name": "ExistingAgent",
            "role": "Assistant",
            "description": "Test",
            "enabled": True,
        }]
    }])
    
    service = AgentCreationService(surreal_client=mock_surreal)
    payload = create_payload("ExistingAgent")

    result = await service.create_agent(payload)

    assert result["success"] is False
    assert "already exists" in result["error"]


@pytest.mark.asyncio
async def test_create_agent_with_llm_config():
    mock_surreal = create_mock_surreal()
    service = AgentCreationService(surreal_client=mock_surreal)

    payload = create_payload(
        "LLMAgent",
        model="openai/gpt-4",
        temperature=0.5,
        max_tokens=4096,
        base_url="https://api.openai.com/v1",
    )

    result = await service.create_agent(payload)

    assert result["success"] is True


@pytest.mark.asyncio
async def test_list_agents_from_db():
    mock_surreal = MagicMock()
    mock_surreal._call = AsyncMock(return_value=[{
        "result": [
            {"name": "Agent1", "role": "Assistant"},
            {"name": "Agent2", "role": "Analyst"},
        ]
    }])
    
    service = AgentCreationService(surreal_client=mock_surreal)

    result = await service.list_agents_from_db()

    assert len(result) == 2
    assert result[0]["name"] == "Agent1"
    assert result[1]["name"] == "Agent2"


@pytest.mark.asyncio
async def test_list_agents_from_db_empty():
    mock_surreal = create_mock_surreal()
    service = AgentCreationService(surreal_client=mock_surreal)

    result = await service.list_agents_from_db()

    assert result == []


@pytest.mark.asyncio
async def test_get_agent_success():
    mock_surreal = MagicMock()
    mock_surreal._call = AsyncMock(return_value=[{
        "result": [{"name": "TestAgent", "role": "Assistant"}]
    }])
    
    service = AgentCreationService(surreal_client=mock_surreal)

    result = await service.get_agent("TestAgent")

    assert result["success"] is True
    assert result["agent"]["name"] == "TestAgent"


@pytest.mark.asyncio
async def test_get_agent_not_found():
    mock_surreal = create_mock_surreal()
    service = AgentCreationService(surreal_client=mock_surreal)

    result = await service.get_agent("NonExistent")

    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_delete_agent_success():
    mock_surreal = create_mock_surreal()
    service = AgentCreationService(surreal_client=mock_surreal)

    result = await service.delete_agent("TestAgent")

    assert result["success"] is True
    assert "deleted" in result["message"]


@pytest.mark.asyncio
async def test_delete_agent_with_registry():
    mock_surreal = create_mock_surreal()
    
    mock_agent = MagicMock()
    mock_agent.stop = AsyncMock()
    
    mock_registry = MagicMock()
    mock_registry.agents = {"TestAgent": mock_agent}
    
    service = AgentCreationService(surreal_client=mock_surreal, agent_registry=mock_registry)

    result = await service.delete_agent("TestAgent")

    assert result["success"] is True
    mock_agent.stop.assert_called_once()
    assert "TestAgent" not in mock_registry.agents


@pytest.mark.asyncio
async def test_create_agent_hotplug_with_folder():
    mock_surreal = create_mock_surreal()
    mock_plugin_loader = MagicMock()
    mock_plugin_loader.load_agent_from_folder = AsyncMock()
    
    service = AgentCreationService(surreal_client=mock_surreal, plugin_loader=mock_plugin_loader)
    
    payload = create_payload("HotplugAgent", agents_folder="/path/to/agent")

    result = await service.create_agent(payload)

    assert result["success"] is True
    mock_plugin_loader.load_agent_from_folder.assert_called_once_with("/path/to/agent")


@pytest.mark.asyncio
async def test_create_agent_hotplug_creates_folder():
    mock_surreal = create_mock_surreal()
    mock_plugin_loader = MagicMock()
    mock_plugin_loader.create_agent_folder = AsyncMock(return_value="/created/agent/path")
    mock_plugin_loader.load_agent_from_folder = AsyncMock()
    
    service = AgentCreationService(surreal_client=mock_surreal, plugin_loader=mock_plugin_loader)
    
    payload = create_payload("AutoAgent")

    result = await service.create_agent(payload)

    assert result["success"] is True
    mock_plugin_loader.create_agent_folder.assert_called_once()
    mock_plugin_loader.load_agent_from_folder.assert_called_once()


@pytest.mark.asyncio
async def test_startup_load_enabled_agents():
    mock_surreal = MagicMock()
    mock_surreal._call = AsyncMock(return_value=[{
        "result": [
            {"name": "EnabledAgent1", "role": "Assistant", "description": "Test", "enabled": True, "prompt": "You are helpful"},
            {"name": "EnabledAgent2", "role": "Analyst", "description": "Test", "enabled": True, "prompt": "You are analytical"},
        ]
    }])
    
    repository = AgentCreationRepository(mock_surreal)

    result = await repository.get_enabled_agents()

    assert len(result) == 2
    assert result[0].name == "EnabledAgent1"
    assert result[0].enabled is True


@pytest.mark.asyncio
async def test_agent_creation_payload_to_agent_config():
    payload = create_payload(
        name="ConfigTest",
        role="Tester",
        model="ollama/mistral",
        temperature=0.8,
    )

    config = payload.to_agent_config()

    assert config["name"] == "ConfigTest"
    assert config["role"] == "Tester"
    assert config["llm_config"]["model"] == "ollama/mistral"
    assert config["llm_config"]["temperature"] == 0.8
    assert config["personified"] is True


@pytest.mark.asyncio
async def test_agent_creation_payload_to_manifest():
    payload = create_payload(
        name="ManifestAgent",
        role="Helper",
        model="openai/gpt-4",
        temperature=0.6,
    )

    manifest = payload.to_manifest_dict()

    assert manifest["id"] == "ManifestAgent"
    assert manifest["name"] == "ManifestAgent"
    assert manifest["role"] == "Helper"
    assert manifest["llm_config"]["model"] == "openai/gpt-4"
    assert manifest["enabled"] is True


@pytest.mark.asyncio
async def test_agent_creation_payload_validation():
    with pytest.raises(ValueError):
        AgentCreationPayload(
            name="BadAgent",
            role="Test",
            base_url="not-a-url",
        )


@pytest.mark.asyncio
async def test_agent_creation_payload_valid_base_url():
    payload = AgentCreationPayload(
        name="GoodAgent",
        role="Test",
        base_url="https://api.example.com",
    )
    assert payload.base_url == "https://api.example.com"

    payload2 = AgentCreationPayload(
        name="GoodAgent2",
        role="Test",
        base_url="http://localhost:8000",
    )
    assert payload2.base_url == "http://localhost:8000"
