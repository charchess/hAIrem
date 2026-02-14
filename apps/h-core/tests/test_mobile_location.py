import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from src.features.home.spatial.mobile.models import MobileLocationUpdate, MobileClientInfo, LocationThrottleConfig
from src.features.home.spatial.mobile.service import ThrottleTracker, MobileLocationService
from src.features.home.spatial.location.service import LocationService


class TestThrottleTracker:
    @pytest.fixture
    def config(self):
        return LocationThrottleConfig(min_interval_seconds=5, max_updates_per_minute=10)

    @pytest.mark.asyncio
    async def test_first_update_allowed(self, config):
        tracker = ThrottleTracker(config)
        result = await tracker.is_allowed("client-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_rapid_updates_throttled(self, config):
        tracker = ThrottleTracker(config)
        
        await tracker.is_allowed("client-1")
        result = await tracker.is_allowed("client-1")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_different_clients_not_throttled(self, config):
        tracker = ThrottleTracker(config)
        
        await tracker.is_allowed("client-1")
        result = await tracker.is_allowed("client-2")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_max_updates_per_minute(self, config):
        config.max_updates_per_minute = 3
        config.min_interval_seconds = 0
        tracker = ThrottleTracker(config)
        
        assert await tracker.is_allowed("client-1") is True
        assert await tracker.is_allowed("client-1") is True
        assert await tracker.is_allowed("client-1") is True
        assert await tracker.is_allowed("client-1") is False


class TestMobileLocationService:
    @pytest.fixture
    def mock_location_service(self):
        mock = MagicMock()
        mock.update_agent_location = AsyncMock(return_value={"success": True})
        del mock.track_ambiguous_location
        return mock

    @pytest.fixture
    def throttle_config(self):
        return LocationThrottleConfig(min_interval_seconds=1, max_updates_per_minute=100)

    @pytest.mark.asyncio
    async def test_register_client(self, mock_location_service, throttle_config):
        service = MobileLocationService(mock_location_service, throttle_config)
        await service.initialize()
        
        client_info = await service.register_client("client-1", "agent-1")
        
        assert client_info.client_id == "client-1"
        assert client_info.agent_id == "agent-1"
        assert client_info.is_connected is True

    @pytest.mark.asyncio
    async def test_handle_location_update_with_room(self, mock_location_service, throttle_config):
        service = MobileLocationService(mock_location_service, throttle_config)
        await service.initialize()
        await service.register_client("client-1", "agent-1")
        
        location = MobileLocationUpdate(
            agent_id="agent-1",
            latitude=37.7749,
            longitude=-122.4194,
            room_id="living-room",
            source="gps",
            accuracy=5.0
        )
        
        result = await service.handle_location_update("client-1", location)
        
        assert result["success"] is True
        assert result["location"]["room_id"] == "living-room"
        mock_location_service.update_agent_location.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_location_update_coordinates_only(self, mock_location_service, throttle_config):
        service = MobileLocationService(mock_location_service, throttle_config)
        await service.initialize()
        await service.register_client("client-1", "agent-1")
        
        location = MobileLocationUpdate(
            agent_id="agent-1",
            latitude=37.7749,
            longitude=-122.4194,
            source="gps"
        )
        
        result = await service.handle_location_update("client-1", location)
        
        assert result["success"] is True
        assert result["location"]["latitude"] == 37.7749
        assert result["location"]["longitude"] == -122.4194

    @pytest.mark.asyncio
    async def test_handle_location_update_throttled(self, mock_location_service, throttle_config):
        throttle_config.min_interval_seconds = 3600
        service = MobileLocationService(mock_location_service, throttle_config)
        await service.initialize()
        await service.register_client("client-1", "agent-1")
        
        location = MobileLocationUpdate(
            agent_id="agent-1",
            room_id="kitchen"
        )
        
        await service.handle_location_update("client-1", location)
        result = await service.handle_location_update("client-1", location)
        
        assert result["success"] is False
        assert result["error"] == "throttled"

    @pytest.mark.asyncio
    async def test_handle_location_update_client_not_registered(self, mock_location_service, throttle_config):
        service = MobileLocationService(mock_location_service, throttle_config)
        await service.initialize()
        
        location = MobileLocationUpdate(
            agent_id="agent-1",
            room_id="kitchen"
        )
        
        result = await service.handle_location_update("unknown-client", location)
        
        assert result["success"] is False
        assert result["error"] == "client_not_registered"

    @pytest.mark.asyncio
    async def test_handle_disconnect_preserves_location(self, mock_location_service, throttle_config):
        service = MobileLocationService(mock_location_service, throttle_config)
        await service.initialize()
        await service.register_client("client-1", "agent-1")
        
        location = MobileLocationUpdate(
            agent_id="agent-1",
            latitude=37.7749,
            longitude=-122.4194,
            room_id="bedroom"
        )
        await service.handle_location_update("client-1", location)
        
        client_info = await service.handle_disconnect("client-1")
        
        assert client_info.is_connected is False
        assert client_info.last_room_id == "bedroom"
        assert client_info.last_latitude == 37.7749

    @pytest.mark.asyncio
    async def test_handle_disconnect_unknown_client(self, mock_location_service, throttle_config):
        service = MobileLocationService(mock_location_service, throttle_config)
        await service.initialize()
        
        result = await service.handle_disconnect("unknown-client")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_client_info(self, mock_location_service, throttle_config):
        service = MobileLocationService(mock_location_service, throttle_config)
        await service.initialize()
        await service.register_client("client-1", "agent-1")
        
        client_info = await service.get_client_info("client-1")
        
        assert client_info is not None
        assert client_info.client_id == "client-1"

    @pytest.mark.asyncio
    async def test_get_last_known_location(self, mock_location_service, throttle_config):
        service = MobileLocationService(mock_location_service, throttle_config)
        await service.initialize()
        await service.register_client("client-1", "agent-1")
        
        location = MobileLocationUpdate(
            agent_id="agent-1",
            latitude=37.7749,
            longitude=-122.4194,
            room_id="kitchen"
        )
        await service.handle_location_update("client-1", location)
        
        last_location = await service.get_last_known_location("client-1")
        
        assert last_location["latitude"] == 37.7749
        assert last_location["room_id"] == "kitchen"

    @pytest.mark.asyncio
    async def test_get_last_known_location_not_found(self, mock_location_service, throttle_config):
        service = MobileLocationService(mock_location_service, throttle_config)
        await service.initialize()
        
        result = await service.get_last_known_location("unknown-client")
        
        assert result is None
