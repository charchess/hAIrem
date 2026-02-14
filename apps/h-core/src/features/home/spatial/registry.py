import logging
from typing import Optional

from src.features.home.spatial.rooms.service import RoomService
from src.features.home.spatial.location.service import LocationService
from src.features.home.spatial.exterior.service import ExteriorService
from src.features.home.spatial.themes.service import WorldThemeService

logger = logging.getLogger(__name__)


class SpatialRegistry:
    def __init__(
        self,
        room_service: Optional[RoomService] = None,
        location_service: Optional[LocationService] = None,
        exterior_service: Optional[ExteriorService] = None,
        theme_service: Optional[WorldThemeService] = None,
    ):
        self.rooms = room_service
        self.locations = location_service
        self.exterior = exterior_service
        self.themes = theme_service

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

    async def _on_theme_update(self, theme_name: str, theme):
        logger.debug(f"SpatialRegistry: Theme updated to {theme_name}")
