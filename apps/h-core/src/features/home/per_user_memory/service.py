import logging
from typing import Any

logger = logging.getLogger(__name__)


class UserMemoryContext:
    """Manages per-user memory context for agents."""

    def __init__(self):
        self.current_user_id: str | None = None
        self.current_user_name: str | None = None
        self.session_id: str | None = None
        self.user_history: list[dict[str, Any]] = []

    def set_user(self, user_id: str, user_name: str | None = None, session_id: str | None = None):
        """Set the current user context."""
        old_user = self.current_user_id
        self.current_user_id = user_id
        self.current_user_name = user_name
        if session_id:
            self.session_id = session_id
        
        if old_user and old_user != user_id:
            logger.info(f"User context switched: {old_user} -> {user_id}")
            self.user_history.append({
                "from_user": old_user,
                "to_user": user_id,
                "action": "switch"
            })

    def get_user(self) -> tuple[str | None, str | None]:
        """Get current user_id and user_name."""
        return self.current_user_id, self.current_user_name

    def clear(self):
        """Clear the user context."""
        self.current_user_id = None
        self.current_user_name = None
        self.session_id = None

    def has_user(self) -> bool:
        """Check if a user is currently set."""
        return self.current_user_id is not None


class UserMemoryService:
    """Service for managing per-user memory operations."""

    def __init__(self, surreal_client: Any = None):
        self.surreal = surreal_client

    async def store_memory_with_user(
        self,
        fact_data: dict[str, Any],
        user_id: str,
        user_name: str | None = None
    ) -> bool:
        """Store a memory with user association."""
        if not self.surreal:
            logger.warning("SurrealDB client not available")
            return False

        fact_data["user_id"] = user_id
        if user_name:
            fact_data["user_name"] = user_name

        try:
            await self.surreal.insert_graph_memory(fact_data)
            return True
        except Exception as e:
            logger.error(f"Failed to store user memory: {e}")
            return False

    async def get_user_memories(
        self,
        user_id: str,
        embedding: list[float],
        limit: int = 3
    ) -> list[dict[str, Any]]:
        """Get memories for a specific user."""
        if not self.surreal:
            return []

        try:
            return await self.surreal.semantic_search_user(embedding, user_id, limit)
        except Exception as e:
            logger.error(f"Failed to get user memories: {e}")
            return []

    async def get_universal_memories(
        self,
        embedding: list[float],
        limit: int = 3
    ) -> list[dict[str, Any]]:
        """Get universal memories (not tied to any specific user)."""
        if not self.surreal:
            return []

        try:
            return await self.surreal.semantic_search_universal(embedding, limit)
        except Exception as e:
            logger.error(f"Failed to get universal memories: {e}")
            return []
