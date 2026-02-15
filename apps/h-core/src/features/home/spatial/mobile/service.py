import logging
import asyncio
from typing import Optional, Dict
from datetime import datetime, timedelta, UTC

from src.features.home.spatial.mobile.models import MobileLocationUpdate, MobileClientInfo, LocationThrottleConfig
from src.features.home.spatial.location.service import LocationService
from src.features.home.spatial.exterior.service import ExteriorService

logger = logging.getLogger(__name__)


class ThrottleTracker:
    def __init__(self, config: LocationThrottleConfig):
        self.config = config
        self._last_update_time: Dict[str, datetime] = {}
        self._update_count: Dict[str, list] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_id: str) -> bool:
        async with self._lock:
            now = datetime.now(UTC)
            
            if client_id not in self._update_count:
                self._update_count[client_id] = []
            
            self._update_count[client_id] = [
                t for t in self._update_count[client_id]
                if now - t < timedelta(minutes=1)
            ]
            
            if len(self._update_count[client_id]) >= self.config.max_updates_per_minute:
                return False
            
            last_time = self._last_update_time.get(client_id)
            if last_time and (now - last_time).total_seconds() < self.config.min_interval_seconds:
                return False
            
            self._last_update_time[client_id] = now
            self._update_count[client_id].append(now)
            
            return True


class MobileLocationService:
    def __init__(self, location_service: LocationService, throttle_config: Optional[LocationThrottleConfig] = None, exterior_service: Optional[ExteriorService] = None):
        self.location_service = location_service
        self.exterior_service = exterior_service
        self.throttle_config = throttle_config or LocationThrottleConfig()
        self.throttle_tracker = ThrottleTracker(self.throttle_config)
        self._mobile_clients: Dict[str, MobileClientInfo] = {}
        self._lock = asyncio.Lock()

    async def initialize(self):
        logger.info("MobileLocationService: Initializing...")

    async def register_client(self, client_id: str, agent_id: str) -> MobileClientInfo:
        async with self._lock:
            client_info = MobileClientInfo(
                client_id=client_id,
                agent_id=agent_id,
                last_seen=datetime.now(UTC),
                is_connected=True
            )
            self._mobile_clients[client_id] = client_info
            logger.info(f"MobileLocationService: Registered client {client_id} for agent {agent_id}")
            return client_info

    async def handle_location_update(
        self,
        client_id: str,
        location: MobileLocationUpdate
    ) -> dict:
        if not await self.throttle_tracker.is_allowed(client_id):
            logger.debug(f"MobileLocationService: Throttled location update from {client_id}")
            return {"success": False, "error": "throttled", "message": "Location update frequency too high"}

        async with self._lock:
            client_info = self._mobile_clients.get(client_id)
            if not client_info:
                return {"success": False, "error": "client_not_registered", "message": "Client not registered"}

            client_info.last_seen = datetime.now(UTC)
            client_info.is_connected = True

            if location.latitude is not None:
                client_info.last_latitude = location.latitude
            if location.longitude is not None:
                client_info.last_longitude = location.longitude
            if location.room_id is not None:
                client_info.last_room_id = location.room_id

        if self.exterior_service and location.latitude is not None:
            spatial_context = await self.exterior_service.handle_location_update(
                agent_id=location.agent_id,
                latitude=location.latitude,
                longitude=location.longitude,
                accuracy=location.accuracy,
                source=location.source or "manual",
                room_id=location.room_id,
                satellites=location.satellites,
                speed=location.speed,
                is_wifi_connected=location.is_wifi_connected,
                ssid=location.wifi_ssid,
            )
            logger.info(f"MobileLocationService: Spatial context for {location.agent_id}: exterior={spatial_context.is_exterior}, theme={spatial_context.exterior_theme}")

        if location.room_id:
            confidence_level = "high" if location.source == "gps" else "medium"
            confidence_reason = f"Source: {location.source}"
            if location.accuracy is not None:
                confidence_reason += f", Accuracy: {location.accuracy}m"

            result = await self.location_service.update_agent_location(
                agent_id=location.agent_id,
                room_id=location.room_id,
                confidence=self.location_service.track_ambiguous_location(
                    location.agent_id, location.room_id, confidence_level, confidence_reason
                ).get("location", {}).get("confidence") if hasattr(self.location_service, 'track_ambiguous_location') else None
            )

            logger.info(f"MobileLocationService: Updated location for agent {location.agent_id} to room {location.room_id}")
            return {
                "success": True,
                "location": {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "room_id": location.room_id,
                    "timestamp": location.timestamp.isoformat() if location.timestamp else datetime.now(UTC).isoformat()
                }
            }

        return {
            "success": True,
            "message": "Location coordinates received",
            "location": {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "accuracy": location.accuracy,
                "source": location.source,
                "timestamp": location.timestamp.isoformat() if location.timestamp else datetime.now(UTC).isoformat()
            }
        }

    async def handle_disconnect(self, client_id: str) -> Optional[MobileClientInfo]:
        async with self._lock:
            client_info = self._mobile_clients.get(client_id)
            if client_info:
                client_info.is_connected = False
                logger.info(f"MobileLocationService: Client {client_id} disconnected, last location preserved: room={client_info.last_room_id}")
            return client_info

    async def get_client_info(self, client_id: str) -> Optional[MobileClientInfo]:
        return self._mobile_clients.get(client_id)

    async def get_last_known_location(self, client_id: str) -> Optional[dict]:
        client_info = self._mobile_clients.get(client_id)
        if not client_info:
            return None

        return {
            "client_id": client_id,
            "agent_id": client_info.agent_id,
            "latitude": client_info.last_latitude,
            "longitude": client_info.last_longitude,
            "room_id": client_info.last_room_id,
            "last_seen": client_info.last_seen.isoformat() if client_info.last_seen else None,
            "is_connected": client_info.is_connected
        }

    async def get_agent_last_location(self, agent_id: str) -> Optional[dict]:
        async with self._lock:
            for client_info in self._mobile_clients.values():
                if client_info.agent_id == agent_id and not client_info.is_connected:
                    return {
                        "agent_id": agent_id,
                        "latitude": client_info.last_latitude,
                        "longitude": client_info.last_longitude,
                        "room_id": client_info.last_room_id,
                        "last_seen": client_info.last_seen.isoformat() if client_info.last_seen else None
                    }
        return None
