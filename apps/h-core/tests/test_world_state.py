import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


def _make_service(surreal=None, redis=None):
    from src.services.spatial.world_state import WorldStateService

    surreal = surreal or MagicMock()
    surreal._call = AsyncMock(return_value=[{"result": [{"theme": "Default"}]}])

    redis = redis or MagicMock()
    redis.publish_event = AsyncMock()

    return WorldStateService(surreal_client=surreal, redis_client=redis), surreal, redis


@pytest.mark.asyncio
async def test_world_state_set_theme_updates_internal_state():
    svc, _, _ = _make_service()
    await svc.set_theme("soiree_halloween")
    assert svc.get_theme() == "soiree_halloween"


@pytest.mark.asyncio
async def test_world_state_persists_theme_in_surrealdb():
    svc, surreal, _ = _make_service()
    await svc.set_theme("winter_night")
    surreal._call.assert_called_once()
    call_args = surreal._call.call_args
    assert "world_state" in call_args[0][1]


@pytest.mark.asyncio
async def test_world_state_change_triggers_cascade_event():
    svc, _, redis = _make_service()
    await svc.set_theme("soiree_halloween")
    redis.publish_event.assert_called_once()
    call_args = redis.publish_event.call_args
    assert call_args[0][0] == "system_stream"
    payload = call_args[0][1]
    assert payload["type"] == "world.theme_changed"


@pytest.mark.asyncio
async def test_world_state_cascade_event_contains_theme():
    svc, _, redis = _make_service()
    await svc.set_theme("soiree_halloween")
    payload = redis.publish_event.call_args[0][1]
    assert payload["payload"]["content"]["theme"] == "soiree_halloween"


@pytest.mark.asyncio
async def test_world_state_get_theme_default():
    svc, _, _ = _make_service()
    assert svc.get_theme() == "Default"


@pytest.mark.asyncio
async def test_world_state_skips_db_if_no_surreal():
    from src.services.spatial.world_state import WorldStateService

    redis = MagicMock()
    redis.publish_event = AsyncMock()
    svc = WorldStateService(surreal_client=None, redis_client=redis)
    await svc.set_theme("summer")
    assert svc.get_theme() == "summer"
    redis.publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_dieu_change_world_theme_tool_exists():
    from src.models.agent import AgentConfig
    from unittest.mock import AsyncMock, MagicMock

    config = AgentConfig(
        name="Dieu",
        role="Agent invisible",
        system_prompt="Tu es Dieu.",
        capabilities=["proactivity"],
        skills=[
            {
                "name": "change_world_theme",
                "description": "Change le thème global du monde (ex: Christmas, Cyberpunk, Beach).",
            }
        ],
    )
    redis = MagicMock()
    redis.publish = AsyncMock()
    redis.publish_event = AsyncMock()
    llm = MagicMock()
    llm.model = "gpt-4"
    llm.chat = AsyncMock(return_value="ok")

    with patch("src.services.spatial.world_state.WorldStateService") as MockWS:
        mock_ws = MagicMock()
        mock_ws.set_theme = AsyncMock()
        MockWS.return_value = mock_ws

        from entropy.logic import Agent

        agent = Agent(
            config=config,
            redis_client=redis,
            llm_client=llm,
            surreal_client=None,
            visual_service=None,
            agent_registry=None,
        )
        assert "change_world_theme" in agent.tools


@pytest.mark.asyncio
async def test_dieu_change_world_theme_calls_world_state_service():
    from src.models.agent import AgentConfig

    config = AgentConfig(
        name="Dieu",
        role="Agent invisible",
        system_prompt="Tu es Dieu.",
        capabilities=["proactivity"],
        skills=[
            {
                "name": "change_world_theme",
                "description": "Change le thème global du monde (ex: Christmas, Cyberpunk, Beach).",
            }
        ],
    )
    redis = MagicMock()
    redis.publish = AsyncMock()
    redis.publish_event = AsyncMock()
    llm = MagicMock()
    llm.model = "gpt-4"

    with patch("src.services.spatial.world_state.WorldStateService") as MockWS:
        mock_ws = MagicMock()
        mock_ws.set_theme = AsyncMock()
        MockWS.return_value = mock_ws

        from entropy.logic import Agent

        agent = Agent(
            config=config,
            redis_client=redis,
            llm_client=llm,
            surreal_client=None,
            visual_service=None,
            agent_registry=None,
        )
        await agent.change_world_theme("soiree_halloween")
        mock_ws.set_theme.assert_called_once_with("soiree_halloween")
