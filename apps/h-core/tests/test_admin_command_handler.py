import pytest
from unittest.mock import AsyncMock, MagicMock

from src.features.admin.command_handler import AdminCommandHandler


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.publish_event = AsyncMock()
    return r


@pytest.fixture
def mock_skill_mgmt():
    s = MagicMock()
    s.list_skills = AsyncMock(
        return_value=[
            {"skill_name": "home_assistant", "access": "multiple", "tools": ["turn_on"], "active_for": []},
            {"skill_name": "music", "access": "unique", "tools": ["play_music"], "active_for": ["Lisa"]},
        ]
    )
    s.grant = AsyncMock(return_value={"success": True, "persona_id": "Moka", "skill_name": "cooking", "active": True})
    s.revoke = AsyncMock(return_value={"success": True, "persona_id": "Moka", "skill_name": "cooking", "active": False})
    return s


@pytest.fixture
def mock_registry():
    agent = MagicMock()
    agent.config.role = "assistant"
    agent.is_active = True
    agent.personified = True
    agent.tools = {"recall_memory": {"skill_package": None}, "turn_on": {"skill_package": "home_assistant"}}
    r = MagicMock()
    r.agents = {"Lisa": agent}
    return r


@pytest.fixture
def handler(mock_registry, mock_skill_mgmt, mock_redis):
    return AdminCommandHandler(mock_registry, mock_skill_mgmt, mock_redis)


@pytest.mark.asyncio
async def test_handle_skill_list_returns_true(handler):
    result = await handler.handle("admin.skill.list", {})
    assert result is True


@pytest.mark.asyncio
async def test_handle_skill_list_publishes_response(handler, mock_redis, mock_skill_mgmt):
    await handler.handle("admin.skill.list", {})
    mock_skill_mgmt.list_skills.assert_called_once()
    mock_redis.publish_event.assert_called_once()
    event = mock_redis.publish_event.call_args[0][1]
    assert event["type"] == "admin.skill.list.response"
    assert event["payload"]["content"]["success"] is True
    assert len(event["payload"]["content"]["skills"]) == 2


@pytest.mark.asyncio
async def test_handle_skill_grant_calls_service(handler, mock_redis, mock_skill_mgmt):
    await handler.handle("admin.skill.grant", {"persona_id": "Moka", "skill_name": "cooking"})
    mock_skill_mgmt.grant.assert_called_once_with("Moka", "cooking")
    event = mock_redis.publish_event.call_args[0][1]
    assert event["type"] == "admin.skill.grant.response"
    assert event["payload"]["content"]["success"] is True


@pytest.mark.asyncio
async def test_handle_skill_grant_missing_params_returns_error(handler, mock_redis):
    await handler.handle("admin.skill.grant", {"persona_id": "Moka"})
    event = mock_redis.publish_event.call_args[0][1]
    assert event["payload"]["content"]["success"] is False
    assert "required" in event["payload"]["content"]["error"]


@pytest.mark.asyncio
async def test_handle_skill_revoke_calls_service(handler, mock_redis, mock_skill_mgmt):
    await handler.handle("admin.skill.revoke", {"persona_id": "Moka", "skill_name": "cooking"})
    mock_skill_mgmt.revoke.assert_called_once_with("Moka", "cooking")
    event = mock_redis.publish_event.call_args[0][1]
    assert event["type"] == "admin.skill.revoke.response"
    assert event["payload"]["content"]["active"] is False


@pytest.mark.asyncio
async def test_handle_agent_list_returns_true(handler):
    result = await handler.handle("admin.agent.list", {})
    assert result is True


@pytest.mark.asyncio
async def test_handle_agent_list_includes_skills(handler, mock_redis):
    await handler.handle("admin.agent.list", {})
    event = mock_redis.publish_event.call_args[0][1]
    assert event["type"] == "admin.agent.list.response"
    agents = event["payload"]["content"]["agents"]
    assert len(agents) == 1
    assert agents[0]["agent_id"] == "Lisa"
    assert any(t["name"] == "turn_on" for t in agents[0]["skills"])


@pytest.mark.asyncio
async def test_unknown_msg_type_returns_false(handler):
    result = await handler.handle("some.other.type", {})
    assert result is False


@pytest.mark.asyncio
async def test_handle_does_not_call_service_for_non_admin(handler, mock_skill_mgmt):
    await handler.handle("system.heartbeat", {})
    mock_skill_mgmt.list_skills.assert_not_called()
