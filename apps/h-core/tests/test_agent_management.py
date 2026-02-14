import pytest
from unittest.mock import MagicMock, AsyncMock
from src.features.admin.agent_management.service import AgentManagementService
from src.infrastructure.plugin_loader import AgentRegistry
from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig


def create_mock_agent(name: str, role: str = "Assistant", is_active: bool = True, personified: bool = True):
    mock_config = AgentConfig(name=name, role=role)
    mock_redis = MagicMock()
    mock_llm = MagicMock()
    agent = BaseAgent(config=mock_redis, redis_client=mock_redis, llm_client=mock_llm)
    agent.config = mock_config
    agent.is_active = is_active
    agent.personified = personified
    return agent


@pytest.mark.asyncio
async def test_enable_agent_success():
    registry = AgentRegistry()
    agent = create_mock_agent("TestAgent", is_active=False)
    registry.add_agent(agent)

    mock_redis = MagicMock()
    mock_redis.publish_event = AsyncMock()
    service = AgentManagementService(redis_client=mock_redis, agent_registry=registry)

    result = await service.enable_agent("TestAgent")

    assert result["success"] is True
    assert result["agent_id"] == "TestAgent"
    assert result["is_active"] is True
    assert agent.is_active is True


@pytest.mark.asyncio
async def test_disable_agent_success():
    registry = AgentRegistry()
    agent = create_mock_agent("TestAgent", is_active=True)
    registry.add_agent(agent)

    mock_redis = MagicMock()
    mock_redis.publish_event = AsyncMock()
    service = AgentManagementService(redis_client=mock_redis, agent_registry=registry)

    result = await service.disable_agent("TestAgent")

    assert result["success"] is True
    assert result["agent_id"] == "TestAgent"
    assert result["is_active"] is False
    assert agent.is_active is False


@pytest.mark.asyncio
async def test_enable_agent_not_found():
    registry = AgentRegistry()
    mock_redis = MagicMock()
    service = AgentManagementService(redis_client=mock_redis, agent_registry=registry)

    result = await service.enable_agent("NonExistent")

    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_disable_agent_not_found():
    registry = AgentRegistry()
    mock_redis = MagicMock()
    service = AgentManagementService(redis_client=mock_redis, agent_registry=registry)

    result = await service.disable_agent("NonExistent")

    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_agent_unavailable_message():
    registry = AgentRegistry()
    agent = create_mock_agent("UnavailableAgent", is_active=False)
    registry.add_agent(agent)

    mock_redis = MagicMock()
    service = AgentManagementService(redis_client=mock_redis, agent_registry=registry)

    result = await service.get_agent_status("UnavailableAgent")

    assert result["success"] is True
    assert result["is_active"] is False


@pytest.mark.asyncio
async def test_re_enable_agent_restores_functionality():
    registry = AgentRegistry()
    agent = create_mock_agent("TestAgent", is_active=False)
    registry.add_agent(agent)

    mock_redis = MagicMock()
    mock_redis.publish_event = AsyncMock()
    service = AgentManagementService(redis_client=mock_redis, agent_registry=registry)

    result_disable = await service.disable_agent("TestAgent")
    assert result_disable["is_active"] is False

    result_enable = await service.enable_agent("TestAgent")
    assert result_enable["success"] is True
    assert result_enable["is_active"] is True

    status = await service.get_agent_status("TestAgent")
    assert status["is_active"] is True


@pytest.mark.asyncio
async def test_arbiter_service_called_on_enable():
    registry = AgentRegistry()
    agent = create_mock_agent("TestAgent", is_active=False)
    registry.add_agent(agent)

    mock_redis = MagicMock()
    mock_redis.publish_event = AsyncMock()
    mock_arbiter = MagicMock()
    mock_arbiter.set_agent_status = MagicMock()
    service = AgentManagementService(redis_client=mock_redis, agent_registry=registry, arbiter_service=mock_arbiter)

    await service.enable_agent("TestAgent")

    mock_arbiter.set_agent_status.assert_called_once_with("TestAgent", True)


@pytest.mark.asyncio
async def test_arbiter_service_called_on_disable():
    registry = AgentRegistry()
    agent = create_mock_agent("TestAgent", is_active=True)
    registry.add_agent(agent)

    mock_redis = MagicMock()
    mock_redis.publish_event = AsyncMock()
    mock_arbiter = MagicMock()
    mock_arbiter.set_agent_status = MagicMock()
    service = AgentManagementService(redis_client=mock_redis, agent_registry=registry, arbiter_service=mock_arbiter)

    await service.disable_agent("TestAgent")

    mock_arbiter.set_agent_status.assert_called_once_with("TestAgent", False)


@pytest.mark.asyncio
async def test_list_agents():
    registry = AgentRegistry()
    agent1 = create_mock_agent("Agent1", is_active=True)
    agent2 = create_mock_agent("Agent2", is_active=False)
    registry.add_agent(agent1)
    registry.add_agent(agent2)

    mock_redis = MagicMock()
    service = AgentManagementService(redis_client=mock_redis, agent_registry=registry)

    result = await service.list_agents()

    assert len(result) == 2
    agent_ids = [a["agent_id"] for a in result]
    assert "Agent1" in agent_ids
    assert "Agent2" in agent_ids
