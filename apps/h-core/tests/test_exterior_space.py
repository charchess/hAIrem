import pytest
from unittest.mock import AsyncMock, MagicMock
from src.features.home.spatial.exterior.service import ExteriorService, EXTERIOR_THEMES
from src.features.home.spatial.exterior.models import ExteriorConfig, ExteriorDetectionResult, AgentSpatialContext
from src.features.home.spatial.location.service import LocationService


class TestDetectExterior:
    @pytest.fixture
    def mock_location_service(self):
        return MagicMock(spec=LocationService)

    @pytest.fixture
    def exterior_service(self, mock_location_service):
        config = ExteriorConfig(
            gps_accuracy_threshold=20.0,
            min_satellites_for_exterior=5,
            high_speed_threshold=2.0,
            wifi_interior_indicator=True,
        )
        return ExteriorService(mock_location_service, config)

    def test_high_satellites_detects_exterior(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=10.0,
            source="gps",
            satellites=8,
        )
        assert result.is_exterior is True
        assert result.confidence > 0

    def test_low_gps_accuracy_detects_exterior(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=50.0,
            source="gps",
        )
        assert result.is_exterior is True

    def test_high_gps_accuracy_detects_interior(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=5.0,
            source="gps",
        )
        assert result.is_exterior is False

    def test_wifi_connected_detects_interior(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=10.0,
            source="network",
            is_wifi_connected=True,
        )
        assert result.is_exterior is False

    def test_no_wifi_detects_exterior(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=10.0,
            source="network",
            is_wifi_connected=False,
            satellites=6,
        )
        assert result.is_exterior is True

    def test_high_speed_detects_exterior(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=10.0,
            source="gps",
            speed=5.0,
        )
        assert result.is_exterior is True

    def test_public_wifi_detects_exterior(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=10.0,
            source="network",
            ssid="Free_WiFi",
            satellites=6,
        )
        assert result.is_exterior is True

    def test_low_satellites_suggests_interior(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=10.0,
            source="gps",
            satellites=3,
        )
        assert result.is_exterior is False

    def test_detection_method_gps_accuracy(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=10.0,
            source="gps",
        )
        assert result.detection_method == "gps_accuracy"

    def test_detection_method_satellites(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=None,
            source="gps",
            satellites=8,
        )
        assert result.detection_method == "satellites"

    def test_detection_method_network(self, exterior_service):
        result = exterior_service.detect_exterior(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=None,
            source="network",
            is_wifi_connected=False,
        )
        assert result.detection_method == "network"


class TestGetAgentContextPrompt:
    @pytest.fixture
    def mock_location_service(self):
        return MagicMock(spec=LocationService)

    @pytest.fixture
    def exterior_service(self, mock_location_service):
        return ExteriorService(mock_location_service)

    def test_exterior_context_returns_prompt(self, exterior_service):
        exterior_service._agent_contexts["agent-1"] = AgentSpatialContext(
            agent_id="agent-1",
            is_exterior=True,
            exterior_theme="outdoor",
        )
        
        prompt = exterior_service.get_agent_context_prompt("agent-1")
        
        assert "[Spatial Context]" in prompt
        assert "outdoor" in prompt.lower()

    def test_interior_context_with_room_returns_prompt(self, exterior_service):
        exterior_service._agent_contexts["agent-1"] = AgentSpatialContext(
            agent_id="agent-1",
            is_exterior=False,
            current_room_id="living-room",
        )
        
        prompt = exterior_service.get_agent_context_prompt("agent-1")
        
        assert "[Spatial Context]" in prompt
        assert "living-room" in prompt

    def test_no_context_returns_empty_string(self, exterior_service):
        prompt = exterior_service.get_agent_context_prompt("unknown-agent")
        assert prompt == ""

    def test_exterior_without_theme_uses_default(self, exterior_service):
        exterior_service._agent_contexts["agent-1"] = AgentSpatialContext(
            agent_id="agent-1",
            is_exterior=True,
            exterior_theme=None,
        )
        
        prompt = exterior_service.get_agent_context_prompt("agent-1")
        
        assert "outdoors" in prompt.lower()


class TestUpdateAgentSpatialContext:
    @pytest.fixture
    def mock_location_service(self):
        return MagicMock(spec=LocationService)

    @pytest.fixture
    def exterior_service(self, mock_location_service):
        return ExteriorService(mock_location_service)

    @pytest.mark.asyncio
    async def test_creates_new_context_for_new_agent(self, exterior_service):
        detection = ExteriorDetectionResult(
            is_exterior=True,
            confidence=0.8,
            detection_method="satellites",
            markers={"satellites": 8},
        )
        
        context = await exterior_service.update_agent_spatial_context(
            agent_id="agent-new",
            detection_result=detection,
        )
        
        assert context.agent_id == "agent-new"
        assert context.is_exterior is True
        assert context.exterior_theme is not None

    @pytest.mark.asyncio
    async def test_re_entering_indoor_clears_exterior_theme(self, exterior_service):
        exterior_service._agent_contexts["agent-1"] = AgentSpatialContext(
            agent_id="agent-1",
            is_exterior=True,
            exterior_theme="outdoor",
        )
        
        detection = ExteriorDetectionResult(
            is_exterior=False,
            confidence=0.9,
            detection_method="gps_accuracy",
            markers={"accuracy": 5.0},
        )
        
        context = await exterior_service.update_agent_spatial_context(
            agent_id="agent-1",
            detection_result=detection,
            room_id="living-room",
        )
        
        assert context.is_exterior is False
        assert context.exterior_theme is None
        assert context.current_room_id == "living-room"

    @pytest.mark.asyncio
    async def test_location_history_tracking(self, exterior_service):
        detection = ExteriorDetectionResult(
            is_exterior=True,
            confidence=0.8,
            detection_method="satellites",
            markers={"satellites": 8},
        )
        
        await exterior_service.update_agent_spatial_context(
            agent_id="agent-1",
            detection_result=detection,
        )
        
        detection2 = ExteriorDetectionResult(
            is_exterior=False,
            confidence=0.9,
            detection_method="gps_accuracy",
            markers={"accuracy": 5.0},
        )
        
        context = await exterior_service.update_agent_spatial_context(
            agent_id="agent-1",
            detection_result=detection2,
            room_id="kitchen",
        )
        
        assert len(context.location_history) == 2
        assert context.location_history[0]["is_exterior"] is True
        assert context.location_history[1]["is_exterior"] is False

    @pytest.mark.asyncio
    async def test_history_limited_to_10_entries(self, exterior_service):
        detection = ExteriorDetectionResult(
            is_exterior=True,
            confidence=0.8,
            detection_method="satellites",
            markers={},
        )
        
        for i in range(15):
            detection.markers = {"iteration": i}
            await exterior_service.update_agent_spatial_context(
                agent_id="agent-1",
                detection_result=detection,
            )
        
        context = exterior_service._agent_contexts["agent-1"]
        assert len(context.location_history) == 10

    @pytest.mark.asyncio
    async def test_exterior_theme_based_on_speed(self, exterior_service):
        detection = ExteriorDetectionResult(
            is_exterior=True,
            confidence=0.8,
            detection_method="gps",
            markers={"speed": 10.0},
        )
        
        context = await exterior_service.update_agent_spatial_context(
            agent_id="agent-1",
            detection_result=detection,
        )
        
        assert context.exterior_theme == EXTERIOR_THEMES["vehicle"]

    @pytest.mark.asyncio
    async def test_exterior_theme_based_on_ssid(self, exterior_service):
        detection = ExteriorDetectionResult(
            is_exterior=True,
            confidence=0.8,
            detection_method="network",
            markers={"ssid": "Park_Guest"},
        )
        
        context = await exterior_service.update_agent_spatial_context(
            agent_id="agent-1",
            detection_result=detection,
        )
        
        assert context.exterior_theme == EXTERIOR_THEMES["park"]
