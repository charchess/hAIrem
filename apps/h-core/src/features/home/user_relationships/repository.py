import logging
from typing import Any

from src.infrastructure.redis import RedisClient

from .models import UserRelationship

logger = logging.getLogger(__name__)


class UserRelationshipRepository:
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.key_prefix = "agent:user:relationship:"

    def _get_key(self, agent_id: str, user_id: str) -> str:
        return f"{self.key_prefix}{agent_id}:{user_id}"

    async def get(self, agent_id: str, user_id: str) -> UserRelationship | None:
        key = self._get_key(agent_id, user_id)
        try:
            data = await self.redis.get(key)
            if data:
                return UserRelationship.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Error getting user relationship: {e}")
            return None

    async def save(self, relationship: UserRelationship) -> bool:
        key = self._get_key(relationship.agent_id, relationship.user_id)
        try:
            await self.redis.set(key, relationship.to_dict())
            return True
        except Exception as e:
            logger.error(f"Error saving user relationship: {e}")
            return False

    async def delete(self, agent_id: str, user_id: str) -> bool:
        key = self._get_key(agent_id, user_id)
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting user relationship: {e}")
            return False

    async def get_all_for_agent(self, agent_id: str) -> list[UserRelationship]:
        pattern = f"{self.key_prefix}{agent_id}:*"
        relationships = []
        try:
            keys = []
            cursor = 0
            while True:
                cursor, found_keys = await self.redis.scan(cursor, pattern, 100)
                keys.extend(found_keys)
                if cursor == 0:
                    break
            
            for key in keys:
                data = await self.redis.get(key)
                if data:
                    relationships.append(UserRelationship.from_dict(data))
        except Exception as e:
            logger.error(f"Error getting relationships for agent: {e}")
        return relationships

    async def get_all_for_user(self, user_id: str) -> list[UserRelationship]:
        pattern = f"{self.key_prefix}*:{user_id}"
        relationships = []
        try:
            keys = []
            cursor = 0
            while True:
                cursor, found_keys = await self.redis.scan(cursor, pattern, 100)
                keys.extend(found_keys)
                if cursor == 0:
                    break
            
            for key in keys:
                data = await self.redis.get(key)
                if data:
                    relationships.append(UserRelationship.from_dict(data))
        except Exception as e:
            logger.error(f"Error getting relationships for user: {e}")
        return relationships
