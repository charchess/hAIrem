import logging
from typing import Optional
from datetime import datetime

from src.features.home.spatial.exterior.models import (
    ExteriorDetectionResult,
    ExteriorMarkers,
    ExteriorConfig,
    AgentSpatialContext,
)
from src.features.home.spatial.location.service import LocationService

logger = logging.getLogger(__name__)


EXTERIOR_THEMES = {
    "outdoor": "User is outdoors - consider weather, activity, and environment in responses",
    "park": "User is in a park or green space - consider outdoor activities and nature",
    "street": "User is on a street - consider traffic, walking, and urban context",
    "vehicle": "User is in a vehicle - consider motion, travel context",
}


class ExteriorService:
    def __init__(
        self,
        location_service: LocationService,
        config: Optional[ExteriorConfig] = None,
    ):
        self.location_service = location_service
        self.config = config or ExteriorConfig()
        self._agent_contexts: dict[str, AgentSpatialContext] = {}

    async def initialize(self):
        logger.info("ExteriorService: Initializing...")

    def detect_exterior(
        self,
        latitude: Optional[float],
        longitude: Optional[float],
        accuracy: Optional[float],
        source: str,
        satellites: Optional[int] = None,
        speed: Optional[float] = None,
        is_wifi_connected: Optional[bool] = None,
        ssid: Optional[str] = None,
    ) -> ExteriorDetectionResult:
        markers = ExteriorMarkers(
            gps_accuracy=accuracy,
            satellites=satellites,
            speed=speed,
            is_wifi_connected=is_wifi_connected,
            ssid=ssid,
        )

        score = 0.0
        max_score = 0.0
        detection_details = []

        max_score += 1.0
        if accuracy is not None:
            if accuracy > self.config.gps_accuracy_threshold:
                score += 1.0
                detection_details.append(f"low_accuracy_outdoor:{accuracy}m")
            else:
                score -= 0.3
                detection_details.append(f"high_accuracy_indoor:{accuracy}m")

        max_score += 1.0
        if satellites is not None and satellites >= self.config.min_satellites_for_exterior:
            score += 0.8
            detection_details.append(f"high_satellites:{satellites}")
        elif satellites is not None:
            score -= 0.2

        max_score += 1.0
        if speed is not None and speed > self.config.high_speed_threshold:
            score += 0.6
            detection_details.append(f"moving:{speed}m/s")

        max_score += 1.0
        if self.config.wifi_interior_indicator:
            if is_wifi_connected:
                score -= 0.5
                detection_details.append("wifi_indoor")
            else:
                score += 0.3
                detection_details.append("no_wifi_outdoor")

        max_score += 1.0
        if ssid:
            known_outdoor_ssids = ["", "Open", "Free", "Guest"]
            if any(ssid.startswith(prefix) for prefix in known_outdoor_ssids):
                score += 0.3
                detection_details.append(f"public_wifi:{ssid}")

        confidence = min(abs(score) / max_score, 1.0) if max_score > 0 else 0.5

        is_exterior = score > 0.3

        method = "hybrid"
        if accuracy is not None and satellites is None and speed is None:
            method = "gps_accuracy"
        elif satellites is not None and accuracy is None:
            method = "satellites"
        elif is_wifi_connected is not None:
            method = "network"

        return ExteriorDetectionResult(
            is_exterior=is_exterior,
            confidence=confidence,
            detection_method=method,
            markers=markers.model_dump(),
        )

    async def update_agent_spatial_context(
        self,
        agent_id: str,
        detection_result: ExteriorDetectionResult,
        room_id: Optional[str] = None,
    ) -> AgentSpatialContext:
        if agent_id not in self._agent_contexts:
            self._agent_contexts[agent_id] = AgentSpatialContext(agent_id=agent_id)

        context = self._agent_contexts[agent_id]
        now = datetime.utcnow()

        was_exterior = context.is_exterior

        context.is_exterior = detection_result.is_exterior

        if detection_result.is_exterior:
            context.last_exterior_time = now
            context.exterior_theme = self._get_exterior_theme(
                detection_result.markers
            )
        else:
            context.last_interior_time = now
            context.exterior_theme = None

        if room_id:
            context.current_room_id = room_id

        context.location_history.append({
            "timestamp": now.isoformat(),
            "is_exterior": detection_result.is_exterior,
            "room_id": room_id,
            "confidence": detection_result.confidence,
        })

        if len(context.location_history) > 10:
            context.location_history = context.location_history[-10:]

        if was_exterior and not detection_result.is_exterior:
            logger.info(f"ExteriorService: Agent {agent_id} returned inside (room: {room_id})")
        elif not was_exterior and detection_result.is_exterior:
            logger.info(f"ExteriorService: Agent {agent_id} went outside")

        return context

    def _get_exterior_theme(self, markers: dict) -> str:
        speed = markers.get("speed")
        if speed and speed > 5.0:
            return EXTERIOR_THEMES.get("vehicle", "outdoor")

        ssid = markers.get("ssid", "").lower()
        if "park" in ssid or "garden" in ssid:
            return EXTERIOR_THEMES.get("park", "outdoor")

        return EXTERIOR_THEMES.get("outdoor")

    def get_agent_spatial_context(self, agent_id: str) -> Optional[AgentSpatialContext]:
        return self._agent_contexts.get(agent_id)

    def get_exterior_context_for_agent(self, agent_id: str) -> Optional[str]:
        context = self._agent_contexts.get(agent_id)
        if context and context.is_exterior and context.exterior_theme:
            return context.exterior_theme
        return None

    def get_agent_context_prompt(self, agent_id: str) -> str:
        """Get a prompt-ready string describing the agent's spatial context."""
        context = self._agent_contexts.get(agent_id)
        if not context:
            return ""

        if context.is_exterior:
            theme = context.exterior_theme or "User is outdoors"
            return f"[Spatial Context] {theme}"

        if context.current_room_id:
            return f"[Spatial Context] User is in {context.current_room_id}"

        return ""

    async def handle_location_update(
        self,
        agent_id: str,
        latitude: Optional[float],
        longitude: Optional[float],
        accuracy: Optional[float],
        source: str,
        room_id: Optional[str] = None,
        satellites: Optional[int] = None,
        speed: Optional[float] = None,
        is_wifi_connected: Optional[bool] = None,
        ssid: Optional[str] = None,
    ) -> AgentSpatialContext:
        detection = self.detect_exterior(
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            source=source,
            satellites=satellites,
            speed=speed,
            is_wifi_connected=is_wifi_connected,
            ssid=ssid,
        )

        context = await self.update_agent_spatial_context(
            agent_id=agent_id,
            detection_result=detection,
            room_id=room_id,
        )

        if not detection.is_exterior and room_id:
            await self.location_service.update_agent_location(
                agent_id=agent_id,
                room_id=room_id,
            )

        return context
