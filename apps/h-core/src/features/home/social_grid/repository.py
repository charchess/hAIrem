import logging
from typing import Any, List, Optional

from src.infrastructure.surrealdb import SurrealDbClient

from .models import RelationshipChangeEvent, RelationshipNotification

logger = logging.getLogger(__name__)


class SocialGridRepository:
    def __init__(self, surreal_client: Optional[SurrealDbClient]):
        self.surreal = surreal_client

    async def setup_schema(self):
        if not self.surreal or not self.surreal.client:
            logger.warning("SurrealDB client not available for social grid schema setup")
            return

        try:
            schema_queries = """
            DEFINE TABLE IF NOT EXISTS relationship_events SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS relationship_type ON TABLE relationship_events TYPE string;
            DEFINE FIELD IF NOT EXISTS party_a ON TABLE relationship_events TYPE string;
            DEFINE FIELD IF NOT EXISTS party_b ON TABLE relationship_events TYPE string;
            DEFINE FIELD IF NOT EXISTS old_status ON TABLE relationship_events TYPE option<string>;
            DEFINE FIELD IF NOT EXISTS new_status ON TABLE relationship_events TYPE option<string>;
            DEFINE FIELD IF NOT EXISTS old_score ON TABLE relationship_events TYPE float;
            DEFINE FIELD IF NOT EXISTS new_score ON TABLE relationship_events TYPE float;
            DEFINE FIELD IF NOT EXISTS change_magnitude ON TABLE relationship_events TYPE string;
            DEFINE FIELD IF NOT EXISTS timestamp ON TABLE relationship_events TYPE datetime DEFAULT time::now();

            DEFINE TABLE IF NOT EXISTS relationship_notifications SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS notification_type ON TABLE relationship_notifications TYPE string;
            DEFINE FIELD IF NOT EXISTS recipient_id ON TABLE relationship_notifications TYPE string;
            DEFINE FIELD IF NOT EXISTS recipient_type ON TABLE relationship_notifications TYPE string;
            DEFINE FIELD IF NOT EXISTS event ON TABLE relationship_notifications TYPE object;
            DEFINE FIELD IF NOT EXISTS message ON TABLE relationship_notifications TYPE string;
            DEFINE FIELD IF NOT EXISTS read ON TABLE relationship_notifications TYPE bool DEFAULT false;
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE relationship_notifications TYPE datetime DEFAULT time::now();

            DEFINE TABLE IF NOT EXISTS social_grid_state SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS agent_user_relationships_count ON TABLE social_grid_state TYPE int;
            DEFINE FIELD IF NOT EXISTS agent_agent_relationships_count ON TABLE social_grid_state TYPE int;
            DEFINE FIELD IF NOT EXISTS pending_notifications ON TABLE social_grid_state TYPE int;
            DEFINE FIELD IF NOT EXISTS last_evolution_timestamp ON TABLE social_grid_state TYPE option<datetime>;
            DEFINE FIELD IF NOT EXISTS loaded_from_db ON TABLE social_grid_state TYPE bool DEFAULT false;
            """
            await self.surreal._call("query", schema_queries)
            logger.info("Social grid schema setup completed")
        except Exception as e:
            logger.error(f"Failed to setup social grid schema: {e}")

    async def save_relationship_event(self, event: RelationshipChangeEvent) -> bool:
        if not self.surreal or not self.surreal.client:
            logger.warning("SurrealDB not available, skipping relationship event save")
            return False

        try:
            data = event.to_dict()
            result = await self.surreal._call("create", "relationship_events", data)
            return result is not None
        except Exception as e:
            logger.error(f"Failed to save relationship event: {e}")
            return False

    async def get_recent_events(
        self,
        relationship_type: Optional[str] = None,
        limit: int = 50
    ) -> List[RelationshipChangeEvent]:
        if not self.surreal or not self.surreal.client:
            return []

        try:
            if relationship_type:
                query = f"SELECT * FROM relationship_events WHERE relationship_type = '{relationship_type}' ORDER BY timestamp DESC LIMIT {limit};"
            else:
                query = f"SELECT * FROM relationship_events ORDER BY timestamp DESC LIMIT {limit};"

            result = await self.surreal._call("query", query)
            if result and isinstance(result, list) and len(result) > 0:
                events_data = result[0].get("result", [])
                return [RelationshipChangeEvent.from_dict(e) for e in events_data]
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
        return []

    async def save_notification(self, notification: RelationshipNotification) -> bool:
        if not self.surreal or not self.surreal.client:
            logger.warning("SurrealDB not available, skipping notification save")
            return False

        try:
            data = notification.to_dict()
            result = await self.surreal._call("create", "relationship_notifications", data)
            return result is not None
        except Exception as e:
            logger.error(f"Failed to save notification: {e}")
            return False

    async def get_notifications_for_recipient(
        self,
        recipient_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[RelationshipNotification]:
        if not self.surreal or not self.surreal.client:
            return []

        try:
            if unread_only:
                query = f"SELECT * FROM relationship_notifications WHERE recipient_id = '{recipient_id}' AND read = false ORDER BY created_at DESC LIMIT {limit};"
            else:
                query = f"SELECT * FROM relationship_notifications WHERE recipient_id = '{recipient_id}' ORDER BY created_at DESC LIMIT {limit};"

            result = await self.surreal._call("query", query)
            if result and isinstance(result, list) and len(result) > 0:
                notifications_data = result[0].get("result", [])
                return [RelationshipNotification.from_dict(n) for n in notifications_data]
        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
        return []

    async def mark_notification_read(self, notification_id: str) -> bool:
        if not self.surreal or not self.surreal.client:
            return False

        try:
            await self.surreal._call("query", f"UPDATE relationship_notifications SET read = true WHERE id = relationship_notifications:`{notification_id}`;")
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False

    async def get_unread_count(self, recipient_id: str) -> int:
        if not self.surreal or not self.surreal.client:
            return 0

        try:
            query = f"SELECT count() FROM relationship_notifications WHERE recipient_id = '{recipient_id}' AND read = false GROUP ALL;"
            result = await self.surreal._call("query", query)
            if result and isinstance(result, list) and len(result) > 0:
                count_data = result[0].get("result", [])
                if count_data and len(count_data) > 0:
                    return count_data[0].get("count", 0)
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
        return 0

    async def save_grid_state(self, state_data: dict[str, Any]) -> bool:
        if not self.surreal or not self.surreal.client:
            return False

        try:
            await self.surreal._call("query", "DELETE FROM social_grid_state;")
            await self.surreal._call("create", "social_grid_state", state_data)
            return True
        except Exception as e:
            logger.error(f"Failed to save grid state: {e}")
            return False

    async def load_grid_state(self) -> Optional[dict[str, Any]]:
        if not self.surreal or not self.surreal.client:
            return None

        try:
            result = await self.surreal._call("query", "SELECT * FROM social_grid_state LIMIT 1;")
            if result and isinstance(result, list) and len(result) > 0:
                states = result[0].get("result", [])
                if states and len(states) > 0:
                    return states[0]
        except Exception as e:
            logger.error(f"Failed to load grid state: {e}")
        return None
