import logging
from typing import Any, Optional

from src.features.home.spatial.rooms.service import RoomService
from src.features.home.spatial.location.service import LocationService
from src.features.home.spatial.exterior.service import ExteriorService
from src.features.home.spatial.themes.service import WorldThemeService
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

logger = logging.getLogger(__name__)


class SpatialRegistry:
    def __init__(
        self,
        room_service: Optional[RoomService] = None,
        location_service: Optional[LocationService] = None,
        exterior_service: Optional[ExteriorService] = None,
        theme_service: Optional[WorldThemeService] = None,
        surreal: Any = None,
        redis: Any = None,
    ):
        self.rooms = room_service
        self.locations = location_service
        self.exterior = exterior_service
        self.themes = theme_service
        self._surreal = surreal
        self._redis = redis

    async def initialize(self):
        logger.info("SpatialRegistry: Initializing...")
        if self.themes:
            await self.themes.initialize()
        if self.exterior:
            await self.exterior.initialize()
        if self.rooms:
            await self.rooms.initialize()
        if self.locations:
            await self.locations.initialize()

    def get_theme_service(self) -> Optional[WorldThemeService]:
        return self.themes

    def get_exterior_service(self) -> Optional[ExteriorService]:
        return self.exterior

    def get_room_service(self) -> Optional[RoomService]:
        return self.rooms

    def get_location_service(self) -> Optional[LocationService]:
        return self.locations

    def register_agent_for_theme_updates(self, agent_id: str):
        if self.themes:
            self.themes.register_theme_callback(agent_id, self._on_theme_update)

    def unregister_agent_from_theme_updates(self, agent_id: str):
        if self.themes:
            self.themes.unregister_theme_callback(agent_id)

    async def move_agent(self, agent_id: str, location_name: str) -> bool:
        success = False
        if self._surreal and hasattr(self._surreal, "move_agent_to_location"):
            success = await self._surreal.move_agent_to_location(agent_id, location_name)
        elif self._surreal:
            await self._surreal.update_agent_state(
                agent_id, "IS_IN", {"name": location_name, "description": f"The {location_name}"}
            )
            success = True

        if self._redis:
            event = HLinkMessage(
                type=MessageType.LOCATION_CHANGED,
                sender=Sender(agent_id=agent_id, role="agent"),
                recipient=Recipient(target="broadcast"),
                payload=Payload(content={"agent_id": agent_id, "location": location_name}),
            )
            try:
                await self._redis.publish_event("system_stream", event.model_dump(mode="json"))
            except Exception as e:
                logger.error(f"SpatialRegistry: location.change broadcast failed — {e}")

        logger.info(f"SpatialRegistry: {agent_id} moved to {location_name}")
        return success

    async def get_agents_in_location(self, location_name: str) -> list[str]:
        if self._surreal and hasattr(self._surreal, "get_agents_in_location"):
            return await self._surreal.get_agents_in_location(location_name)
        return []

    async def _on_theme_update(self, theme_name: str, theme):
        logger.debug(f"SpatialRegistry: Theme updated to {theme_name}")
