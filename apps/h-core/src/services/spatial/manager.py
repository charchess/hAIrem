import logging
from typing import List, Optional
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

logger = logging.getLogger(__name__)


from src.services.visual.bible import bible


class SpatialManager:
    """
    Manages spatial relationships, locations, and global themes (Epic 9).
    """

    def __init__(self, redis_client, surreal_client):
        self.redis = redis_client
        self.surreal = surreal_client
        self.current_theme = "Default"

    async def set_global_theme(self, theme_name: str):
        """
        FR51: World Themes.
        Sets the global narrative/visual theme and broadcasts it.
        """
        logger.info(f"SPATIAL: Changing global theme to '{theme_name}'")
        self.current_theme = theme_name

        # Update Visual Bible
        bible.set_theme(theme_name)

        # Persist to DB
        if self.surreal:
            try:
                await self.surreal._call(
                    "query",
                    "INSERT INTO world_state { id: 'current', theme: $theme } ON DUPLICATE KEY UPDATE theme = $theme;",
                    {"theme": theme_name},
                )
            except Exception as e:
                logger.error(f"SPATIAL: Failed to persist theme to DB: {e}")

        # Broadcast event via system stream (for Bridge/UI)
        msg = HLinkMessage(
            type=MessageType.SYSTEM_STATUS_UPDATE,
            sender=Sender(agent_id="spatial_manager", role="system"),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content={"event": "world_theme_change", "theme": theme_name}),
        )

        try:
            # 1. To Bridge/UI
            res = self.redis.publish_event("system_stream", msg.model_dump(mode="json"))
            if hasattr(res, "__await__"):
                await res

            # 2. To Agents (Internal)
            await self.redis.publish("agent:broadcast", msg)
        except Exception as e:
            logger.warning(f"SPATIAL: Failed to broadcast theme change: {e}")

    async def get_location_occupants(self, location_name: str) -> List[str]:
        """
        FR48: Location Tracking.
        Returns a list of agents currently in a specific location.
        """
        if hasattr(self.surreal, "get_location_occupants"):
            return await self.surreal.get_location_occupants(location_name)

        # Fallback if DB method not implemented yet (or for basic mocks)
        return []

    async def move_agent(self, agent_id: str, location_name: str):
        """Moves an agent to a new location and updates the graph."""
        logger.info(f"SPATIAL: Moving {agent_id} to {location_name}")

        if self.surreal:
            try:
                # Update IS_IN relation in graph
                await self.surreal.update_agent_state(
                    agent_id, "IS_IN", {"name": location_name, "description": f"The {location_name}"}
                )

                # Broadcast location change
                msg = HLinkMessage(
                    type=MessageType.SYSTEM_STATUS_UPDATE,
                    sender=Sender(agent_id="spatial_manager", role="system"),
                    recipient=Recipient(target="broadcast"),
                    payload=Payload(
                        content={"event": "location_change", "agent_id": agent_id, "location": location_name}
                    ),
                )
                await self.redis.publish_event("system_stream", msg.model_dump(mode="json"))

            except Exception as e:
                logger.error(f"SPATIAL: Failed to update agent location in DB: {e}")
