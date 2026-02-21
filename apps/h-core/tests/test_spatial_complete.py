import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_spatial_manager(surreal=None, redis=None):
    from src.services.spatial.manager import SpatialManager

    surreal = surreal or MagicMock()
    surreal._call = AsyncMock(return_value=[])
    surreal.update_agent_state = AsyncMock(return_value=True)
    surreal.get_location_occupants = AsyncMock(return_value=["Lisa", "Renarde"])

    redis = redis or MagicMock()
    redis.publish_event = AsyncMock()
    redis.publish = AsyncMock()

    return SpatialManager(redis_client=redis, surreal_client=surreal), surreal, redis


@pytest.mark.asyncio
async def test_spatial_manager_move_agent_calls_update_state():
    mgr, surreal, _ = _make_spatial_manager()
    await mgr.move_agent("Lisa", "salon")
    surreal.update_agent_state.assert_called_once_with("Lisa", "IS_IN", {"name": "salon", "description": "The salon"})


@pytest.mark.asyncio
async def test_spatial_manager_move_agent_broadcasts_event():
    mgr, _, redis = _make_spatial_manager()
    await mgr.move_agent("Lisa", "salon")
    redis.publish_event.assert_called_once()
    payload = redis.publish_event.call_args[0][1]
    assert payload["payload"]["content"]["agent_id"] == "Lisa"
    assert payload["payload"]["content"]["location"] == "salon"


@pytest.mark.asyncio
async def test_spatial_manager_get_location_occupants_returns_list():
    mgr, surreal, _ = _make_spatial_manager()
    result = await mgr.get_location_occupants("salon")
    assert isinstance(result, list)
    assert "Lisa" in result


@pytest.mark.asyncio
async def test_spatial_manager_get_location_occupants_fallback_empty():
    mgr, surreal, _ = _make_spatial_manager()
    del surreal.get_location_occupants
    result = await mgr.get_location_occupants("chambre")
    assert result == []


@pytest.mark.asyncio
async def test_spatial_manager_set_global_theme_persists_to_db():
    mgr, surreal, _ = _make_spatial_manager()
    with patch("src.services.spatial.manager.bible") as mock_bible:
        await mgr.set_global_theme("soiree_halloween")
    surreal._call.assert_called_once()
    assert "world_state" in surreal._call.call_args[0][1]


@pytest.mark.asyncio
async def test_spatial_manager_set_global_theme_updates_current():
    mgr, _, _ = _make_spatial_manager()
    with patch("src.services.spatial.manager.bible"):
        await mgr.set_global_theme("winter_night")
    assert mgr.current_theme == "winter_night"


@pytest.mark.asyncio
async def test_spatial_manager_set_global_theme_broadcasts_event():
    mgr, _, redis = _make_spatial_manager()
    with patch("src.services.spatial.manager.bible"):
        await mgr.set_global_theme("nuit_halloween")
    redis.publish_event.assert_called()
