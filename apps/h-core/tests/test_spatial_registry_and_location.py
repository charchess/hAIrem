import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from features.home.spatial.registry import SpatialRegistry
from features.home.spatial.location.repository import LocationRepository
from features.home.spatial.location.models import AgentLocation, LocationConfidence


def make_surreal(result=None):
    surreal = MagicMock()
    surreal.client = MagicMock()
    surreal._call = AsyncMock(return_value=result if result is not None else [{"result": []}])
    return surreal


class TestSpatialRegistry:
    @pytest.mark.asyncio
    async def test_initialize_all_services(self):
        mock_themes = AsyncMock()
        mock_exterior = AsyncMock()
        mock_rooms = AsyncMock()
        mock_locations = AsyncMock()
        registry = SpatialRegistry(
            room_service=mock_rooms,
            location_service=mock_locations,
            exterior_service=mock_exterior,
            theme_service=mock_themes,
        )
        await registry.initialize()
        mock_themes.initialize.assert_called_once()
        mock_exterior.initialize.assert_called_once()
        mock_rooms.initialize.assert_called_once()
        mock_locations.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_no_services(self):
        registry = SpatialRegistry()
        await registry.initialize()

    @pytest.mark.asyncio
    async def test_initialize_partial_services(self):
        mock_rooms = AsyncMock()
        registry = SpatialRegistry(room_service=mock_rooms)
        await registry.initialize()
        mock_rooms.initialize.assert_called_once()

    def test_get_theme_service(self):
        mock_themes = MagicMock()
        registry = SpatialRegistry(theme_service=mock_themes)
        assert registry.get_theme_service() is mock_themes

    def test_get_theme_service_none(self):
        registry = SpatialRegistry()
        assert registry.get_theme_service() is None

    def test_get_exterior_service(self):
        mock_exterior = MagicMock()
        registry = SpatialRegistry(exterior_service=mock_exterior)
        assert registry.get_exterior_service() is mock_exterior

    def test_get_room_service(self):
        mock_rooms = MagicMock()
        registry = SpatialRegistry(room_service=mock_rooms)
        assert registry.get_room_service() is mock_rooms

    def test_get_location_service(self):
        mock_locations = MagicMock()
        registry = SpatialRegistry(location_service=mock_locations)
        assert registry.get_location_service() is mock_locations

    def test_register_agent_for_theme_updates_with_theme_service(self):
        mock_themes = MagicMock()
        registry = SpatialRegistry(theme_service=mock_themes)
        registry.register_agent_for_theme_updates("agent1")
        mock_themes.register_theme_callback.assert_called_once()

    def test_register_agent_for_theme_updates_no_theme_service(self):
        registry = SpatialRegistry()
        registry.register_agent_for_theme_updates("agent1")

    def test_unregister_agent_from_theme_updates_with_service(self):
        mock_themes = MagicMock()
        registry = SpatialRegistry(theme_service=mock_themes)
        registry.unregister_agent_from_theme_updates("agent1")
        mock_themes.unregister_theme_callback.assert_called_once_with("agent1")

    def test_unregister_agent_from_theme_updates_no_service(self):
        registry = SpatialRegistry()
        registry.unregister_agent_from_theme_updates("agent1")

    @pytest.mark.asyncio
    async def test_on_theme_update(self):
        registry = SpatialRegistry()
        await registry._on_theme_update("dark", MagicMock())


class TestLocationRepository:
    @pytest.mark.asyncio
    async def test_save_location(self):
        surreal = make_surreal()
        repo = LocationRepository(surreal)
        loc = AgentLocation(agent_id="lisa", room_id="r1")
        result = await repo.save_location(loc)
        assert result.agent_id == "lisa"

    @pytest.mark.asyncio
    async def test_save_location_with_confidence(self):
        surreal = make_surreal()
        repo = LocationRepository(surreal)
        loc = AgentLocation(
            agent_id="lisa", room_id="r1", confidence=LocationConfidence(level="high", reason="explicit")
        )
        result = await repo.save_location(loc)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_current_location_found(self):
        surreal = make_surreal(
            [
                {
                    "result": [
                        {
                            "agent_id": "lisa",
                            "room_id": "r1",
                            "timestamp": "2024-01-15T10:00:00",
                            "confidence": {"level": "high", "reason": "explicit"},
                        }
                    ]
                }
            ]
        )
        repo = LocationRepository(surreal)
        result = await repo.get_current_location("lisa")
        assert result is not None
        assert result.agent_id == "lisa"
        assert result.confidence is not None

    @pytest.mark.asyncio
    async def test_get_current_location_found_no_confidence(self):
        surreal = make_surreal(
            [{"result": [{"agent_id": "lisa", "room_id": "r1", "timestamp": "2024-01-15T10:00:00"}]}]
        )
        repo = LocationRepository(surreal)
        result = await repo.get_current_location("lisa")
        assert result is not None
        assert result.confidence is None

    @pytest.mark.asyncio
    async def test_get_current_location_not_found(self):
        surreal = make_surreal([{"result": []}])
        repo = LocationRepository(surreal)
        result = await repo.get_current_location("unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_location_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = LocationRepository(surreal)
        result = await repo.get_current_location("lisa")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_location_history_with_results(self):
        surreal = make_surreal(
            [
                {
                    "result": [
                        {
                            "agent_id": "lisa",
                            "room_id": "r1",
                            "timestamp": "2024-01-15T10:00:00",
                            "confidence": {"level": "high", "reason": "x"},
                        },
                        {"agent_id": "lisa", "room_id": "r2", "timestamp": "2024-01-14T10:00:00"},
                    ]
                }
            ]
        )
        repo = LocationRepository(surreal)
        result = await repo.get_location_history("lisa")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_location_history_empty(self):
        surreal = make_surreal([{"result": []}])
        repo = LocationRepository(surreal)
        result = await repo.get_location_history("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_location_history_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = LocationRepository(surreal)
        result = await repo.get_location_history("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_recent_locations_with_results(self):
        surreal = make_surreal(
            [
                {
                    "result": [
                        {
                            "agent_id": "lisa",
                            "room_id": "r1",
                            "timestamp": "2024-01-15T10:00:00",
                            "confidence": {"level": "medium", "reason": "inferred"},
                        },
                    ]
                }
            ]
        )
        repo = LocationRepository(surreal)
        since = datetime.utcnow() - timedelta(hours=24)
        result = await repo.get_recent_locations("lisa", since)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_recent_locations_empty(self):
        surreal = make_surreal([{"result": []}])
        repo = LocationRepository(surreal)
        since = datetime.utcnow() - timedelta(hours=1)
        result = await repo.get_recent_locations("lisa", since)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_recent_locations_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = LocationRepository(surreal)
        since = datetime.utcnow() - timedelta(hours=1)
        result = await repo.get_recent_locations("lisa", since)
        assert result == []
