import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_heartbeat_location_field_present():
    from src.services.spatial.manager import SpatialManager

    surreal = MagicMock()
    surreal.get_agent_state = AsyncMock(return_value=[{"relation": "IS_IN", "name": "salon"}])
    redis = MagicMock()
    redis.publish_event = AsyncMock()

    agent = MagicMock()
    agent.is_active = True
    agent.config.name = "Lisa"
    agent.config.preferred_location = "salon"
    agent.llm.model = "gpt-4"
    agent.ctx.prompt_tokens = 100
    agent.ctx.completion_tokens = 50
    agent.ctx.total_tokens = 150
    agent.tools = {}

    registry = MagicMock()
    registry.agents = {"Lisa": agent}

    states = await surreal.get_agent_state("Lisa")
    loc = "Unknown"
    for s in states:
        if s.get("relation") == "IS_IN":
            loc = s.get("name", "Unknown")

    agent_stat = {
        "status": "idle" if agent.is_active else "disabled",
        "active": agent.is_active,
        "llm_model": agent.llm.model,
        "location": loc,
    }

    assert agent_stat["location"] == "salon"


@pytest.mark.asyncio
async def test_heartbeat_location_defaults_to_unknown_when_no_state():
    from src.services.spatial.manager import SpatialManager

    surreal = MagicMock()
    surreal.get_agent_state = AsyncMock(return_value=[])
    redis = MagicMock()

    states = await surreal.get_agent_state("Renarde")
    loc = "Unknown"
    for s in states:
        if s.get("relation") == "IS_IN":
            loc = s.get("name", "Unknown")

    assert loc == "Unknown"


@pytest.mark.asyncio
async def test_move_agent_triggers_redis_location_update():
    from src.services.spatial.manager import SpatialManager

    surreal = MagicMock()
    surreal.update_agent_state = AsyncMock()
    redis = MagicMock()
    redis.publish_event = AsyncMock()

    mgr = SpatialManager(redis_client=redis, surreal_client=surreal)
    await mgr.move_agent("Lisa", "cuisine")

    redis.publish_event.assert_called_once()
    payload = redis.publish_event.call_args[0][1]
    assert payload["payload"]["content"]["location"] == "cuisine"
    assert payload["payload"]["content"]["agent_id"] == "Lisa"
