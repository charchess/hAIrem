import json
import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

EMOTIONAL_HISTORY_KEY_PREFIX = "emotional_history"
EMOTIONAL_ARCHIVE_KEY_PREFIX = "emotional_archive"
EMOTIONAL_HISTORY_THRESHOLD = 20


class EmotionalHistoryRepository:
    def __init__(self, redis_client: Any = None):
        self.redis = redis_client

    def _get_history_key(self, user_id: str) -> str:
        return f"{EMOTIONAL_HISTORY_KEY_PREFIX}:{user_id}"

    def _get_archive_key(self, user_id: str) -> str:
        return f"{EMOTIONAL_ARCHIVE_KEY_PREFIX}:{user_id}"

    async def store_emotional_state(
        self,
        user_id: str,
        emotion: str,
        intensity: float,
        context: str = "",
        keywords: Optional[list[str]] = None,
        agent_id: str = "system",
    ) -> bool:
        if not self.redis or not self.redis.client:
            logger.warning("Redis not available for storing emotional state")
            return False

        try:
            record = {
                "emotion": emotion,
                "intensity": intensity,
                "timestamp": datetime.utcnow().isoformat(),
                "keywords": keywords or [],
                "context": context,
                "user_id": user_id,
                "agent_id": agent_id,
            }
            
            key = self._get_history_key(user_id)
            await self.redis.client.lpush(key, json.dumps(record))
            
            current_length = await self.redis.client.llen(key)
            if current_length > EMOTIONAL_HISTORY_THRESHOLD * 2:
                await self.redis.client.ltrim(key, 0, EMOTIONAL_HISTORY_THRESHOLD - 1)
            
            return True
        except Exception as e:
            logger.error(f"Failed to store emotional state: {e}")
            return False

    async def get_recent_emotions(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if not self.redis or not self.redis.client:
            return []

        try:
            key = self._get_history_key(user_id)
            records = await self.redis.client.lrange(key, 0, limit - 1)
            
            result = []
            for record in records:
                try:
                    result.append(json.loads(record))
                except json.JSONDecodeError:
                    continue
            
            return result
        except Exception as e:
            logger.error(f"Failed to get recent emotions: {e}")
            return []

    async def archive_emotions(
        self,
        user_id: str,
        summary_data: dict[str, Any],
    ) -> bool:
        if not self.redis or not self.redis.client:
            logger.warning("Redis not available for archiving emotions")
            return False

        try:
            key = self._get_archive_key(user_id)
            await self.redis.client.lpush(key, json.dumps(summary_data))
            
            archive_length = await self.redis.client.llen(key)
            if archive_length > 100:
                await self.redis.client.ltrim(key, 0, 99)
            
            return True
        except Exception as e:
            logger.error(f"Failed to archive emotions: {e}")
            return False

    async def get_archived_summaries(
        self,
        user_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if not self.redis or not self.redis.client:
            return []

        try:
            key = self._get_archive_key(user_id)
            records = await self.redis.client.lrange(key, 0, limit - 1)
            
            result = []
            for record in records:
                try:
                    result.append(json.loads(record))
                except json.JSONDecodeError:
                    continue
            
            return result
        except Exception as e:
            logger.error(f"Failed to get archived summaries: {e}")
            return []

    async def clear_history(self, user_id: str) -> bool:
        if not self.redis or not self.redis.client:
            return False

        try:
            key = self._get_history_key(user_id)
            await self.redis.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to clear emotional history: {e}")
            return False
