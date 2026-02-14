import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from src.features.home.spatial.location.models import AgentLocation, LocationConfidence
from src.features.home.spatial.location.repository import LocationRepository
from src.features.home.spatial.location.service import LocationService


class TestLocationConfidenceModel:
    def test_location_confidence_creation(self):
        confidence = LocationConfidence(level="high", reason="GPS signal strong")
        assert confidence.level == "high"
        assert confidence.reason == "GPS signal strong"

    def test_location_confidence_default_level(self):
        confidence = LocationConfidence()
        assert confidence.level == "high"
        assert confidence.reason is None

    def test_location_confidence_medium_level(self):
        confidence = LocationConfidence(level="medium")
        assert confidence.level == "medium"

    def test_location_confidence_low_level(self):
        confidence = LocationConfidence(level="low", reason="Ambiguous location")
        assert confidence.level == "low"
        assert confidence.reason == "Ambiguous location"


class TestAgentLocationModel:
    def test_agent_location_creation(self):
        location = AgentLocation(
            agent_id="agent-1",
            room_id="living-room",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
        )
        assert location.agent_id == "agent-1"
        assert location.room_id == "living-room"
        assert location.timestamp == datetime(2024, 1, 15, 10, 30, 0)
        assert location.confidence is None

    def test_agent_location_with_confidence(self):
        confidence = LocationConfidence(level="medium", reason="WiFi positioning")
        location = AgentLocation(
            agent_id="agent-1",
            room_id="kitchen",
            confidence=confidence,
        )
        assert location.agent_id == "agent-1"
        assert location.room_id == "kitchen"
        assert location.confidence.level == "medium"
        assert location.confidence.reason == "WiFi positioning"


class TestLocationRepository:
    @pytest.fixture
    def mock_surreal(self):
        mock = MagicMock()
        mock._call = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_save_location(self, mock_surreal):
        repo = LocationRepository(mock_surreal)
        location = AgentLocation(
            agent_id="agent-1",
            room_id="living-room",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
        )
        mock_surreal._call.return_value = {"id": "some_id"}
        result = await repo.save_location(location)
        assert result.agent_id == "agent-1"
        assert result.room_id == "living-room"
        mock_surreal._call.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_location_with_confidence(self, mock_surreal):
        repo = LocationRepository(mock_surreal)
        confidence = LocationConfidence(level="low", reason="Test reason")
        location = AgentLocation(
            agent_id="agent-1",
            room_id="bedroom",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            confidence=confidence,
        )
        mock_surreal._call.return_value = {"id": "some_id"}
        result = await repo.save_location(location)
        assert result.confidence.level == "low"
        assert result.confidence.reason == "Test reason"

    @pytest.mark.asyncio
    async def test_get_current_location(self, mock_surreal):
        repo = LocationRepository(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "agent_id": "agent-1",
                    "room_id": "kitchen",
                    "timestamp": "2024-01-15T10:30:00",
                    "confidence": {"level": "high", "reason": None}
                }
            ]
        }]
        result = await repo.get_current_location("agent-1")
        assert result is not None
        assert result.agent_id == "agent-1"
        assert result.room_id == "kitchen"

    @pytest.mark.asyncio
    async def test_get_current_location_not_found(self, mock_surreal):
        repo = LocationRepository(mock_surreal)
        mock_surreal._call.return_value = [{"result": []}]
        result = await repo.get_current_location("agent-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_location_history(self, mock_surreal):
        repo = LocationRepository(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "agent_id": "agent-1",
                    "room_id": "kitchen",
                    "timestamp": "2024-01-15T10:30:00",
                    "confidence": {"level": "high", "reason": None}
                },
                {
                    "agent_id": "agent-1",
                    "room_id": "living-room",
                    "timestamp": "2024-01-15T09:00:00",
                    "confidence": {"level": "medium", "reason": "WiFi"}
                }
            ]
        }]
        result = await repo.get_location_history("agent-1", limit=10)
        assert len(result) == 2
        assert result[0].room_id == "kitchen"
        assert result[1].room_id == "living-room"

    @pytest.mark.asyncio
    async def test_get_location_history_empty(self, mock_surreal):
        repo = LocationRepository(mock_surreal)
        mock_surreal._call.return_value = [{"result": []}]
        result = await repo.get_location_history("agent-1", limit=10)
        assert result == []


class TestLocationService:
    @pytest.fixture
    def mock_surreal(self):
        mock = MagicMock()
        mock._call = AsyncMock()
        return mock

    @pytest.fixture
    def mock_room_service(self):
        mock = MagicMock()
        mock.get_room = AsyncMock(return_value=MagicMock(id="living-room"))
        return mock

    @pytest.mark.asyncio
    async def test_initialize(self, mock_surreal):
        service = LocationService(mock_surreal)
        await service.initialize()
        assert service.repository is not None

    @pytest.mark.asyncio
    async def test_update_agent_location_success(self, mock_surreal, mock_room_service):
        service = LocationService(mock_surreal, mock_room_service)
        mock_surreal._call.return_value = {"id": "some_id"}
        
        result = await service.update_agent_location("agent-1", "living-room")
        
        assert result["success"] is True
        assert result["location"]["agent_id"] == "agent-1"
        assert result["location"]["room_id"] == "living-room"

    @pytest.mark.asyncio
    async def test_update_agent_location_with_confidence(self, mock_surreal, mock_room_service):
        service = LocationService(mock_surreal, mock_room_service)
        mock_surreal._call.return_value = {"id": "some_id"}
        confidence = LocationConfidence(level="medium", reason="Test reason")
        
        result = await service.update_agent_location("agent-1", "kitchen", confidence)
        
        assert result["success"] is True
        assert result["location"]["confidence"]["level"] == "medium"
        assert result["location"]["confidence"]["reason"] == "Test reason"

    @pytest.mark.asyncio
    async def test_update_agent_location_missing_agent_id(self, mock_surreal):
        service = LocationService(mock_surreal)
        
        result = await service.update_agent_location("", "living-room")
        
        assert result["success"] is False
        assert result["error"] == "agent_id is required"

    @pytest.mark.asyncio
    async def test_update_agent_location_missing_room_id(self, mock_surreal):
        service = LocationService(mock_surreal)
        
        result = await service.update_agent_location("agent-1", "")
        
        assert result["success"] is False
        assert result["error"] == "room_id is required"

    @pytest.mark.asyncio
    async def test_update_agent_location_room_not_found(self, mock_surreal, mock_room_service):
        mock_room_service.get_room = AsyncMock(return_value=None)
        service = LocationService(mock_surreal, mock_room_service)
        
        result = await service.update_agent_location("agent-1", "nonexistent-room")
        
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_current_location(self, mock_surreal):
        service = LocationService(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "agent_id": "agent-1",
                    "room_id": "kitchen",
                    "timestamp": "2024-01-15T10:30:00",
                    "confidence": {"level": "high", "reason": None}
                }
            ]
        }]
        
        result = await service.get_current_location("agent-1")
        
        assert result is not None
        assert result["agent_id"] == "agent-1"
        assert result["room_id"] == "kitchen"

    @pytest.mark.asyncio
    async def test_get_current_location_not_found(self, mock_surreal):
        service = LocationService(mock_surreal)
        mock_surreal._call.return_value = [{"result": []}]
        
        result = await service.get_current_location("agent-1")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_location_history(self, mock_surreal):
        service = LocationService(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "agent_id": "agent-1",
                    "room_id": "kitchen",
                    "timestamp": "2024-01-15T10:30:00",
                    "confidence": {"level": "high", "reason": None}
                },
                {
                    "agent_id": "agent-1",
                    "room_id": "living-room",
                    "timestamp": "2024-01-15T09:00:00",
                    "confidence": {"level": "medium", "reason": "WiFi"}
                }
            ]
        }]
        
        result = await service.get_location_history("agent-1", limit=10)
        
        assert len(result) == 2
        assert result[0]["room_id"] == "kitchen"
        assert result[1]["room_id"] == "living-room"
        assert result[1]["confidence"]["level"] == "medium"

    @pytest.mark.asyncio
    async def test_get_location_history_empty(self, mock_surreal):
        service = LocationService(mock_surreal)
        mock_surreal._call.return_value = [{"result": []}]
        
        result = await service.get_location_history("agent-1", limit=10)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_track_ambiguous_location(self, mock_surreal, mock_room_service):
        service = LocationService(mock_surreal, mock_room_service)
        mock_surreal._call.return_value = {"id": "some_id"}
        
        result = await service.track_ambiguous_location(
            agent_id="agent-1",
            room_id="hallway",
            confidence_level="low",
            confidence_reason="Multiple possible rooms"
        )
        
        assert result["success"] is True
        assert result["location"]["room_id"] == "hallway"
        assert result["location"]["confidence"]["level"] == "low"
        assert result["location"]["confidence"]["reason"] == "Multiple possible rooms"

    @pytest.mark.asyncio
    async def test_track_ambiguous_location_default_confidence(self, mock_surreal, mock_room_service):
        service = LocationService(mock_surreal, mock_room_service)
        mock_surreal._call.return_value = {"id": "some_id"}
        
        result = await service.track_ambiguous_location(
            agent_id="agent-1",
            room_id="hallway"
        )
        
        assert result["success"] is True
        assert result["location"]["confidence"]["level"] == "medium"
        assert result["location"]["confidence"]["reason"] is None
