import logging
from typing import Any

from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload
from src.services.visual.bible import bible

logger = logging.getLogger(__name__)

_UPSERT_QUERY = "INSERT INTO world_state { id: 'current', theme: $theme } ON DUPLICATE KEY UPDATE theme = $theme;"


class WorldStateService:
    def __init__(self, surreal_client: Any, redis_client: Any):
        self.surreal = surreal_client
        self.redis = redis_client
        self._current_theme: str = "Default"

    def get_theme(self) -> str:
        return self._current_theme

    async def set_theme(self, theme_name: str) -> None:
        self._current_theme = theme_name
        bible.set_theme(theme_name)

        if self.surreal:
            try:
                await self.surreal._call("query", _UPSERT_QUERY, {"theme": theme_name})
            except Exception as e:
                logger.error(f"WorldStateService: DB persist failed — {e}")

        event = HLinkMessage(
            type=MessageType.WORLD_THEME_CHANGED,
            sender=Sender(agent_id="world_state", role="system"),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content={"theme": theme_name}),
        )
        try:
            await self.redis.publish_event("system_stream", event.model_dump(mode="json"))
        except Exception as e:
            logger.error(f"WorldStateService: Redis broadcast failed — {e}")
