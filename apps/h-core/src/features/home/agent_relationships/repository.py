import logging
from typing import Any

from src.infrastructure.redis import RedisClient

from .models import AgentRelationship

logger = logging.getLogger(__name__)


class RelationshipRepository:
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.key_prefix = "agent:relationship:"

    def _get_key(self, agent_a: str, agent_b: str) -> str:
        sorted_agents = sorted([agent_a, agent_b])
        return f"{self.key_prefix}{sorted_agents[0]}:{sorted_agents[1]}"

    async def get(self, agent_a: str, agent_b: str) -> AgentRelationship | None:
        key = self._get_key(agent_a, agent_b)
        try:
            data = await self.redis.get(key)
            if data:
                return AgentRelationship.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Error getting relationship: {e}")
            return None

    async def save(self, relationship: AgentRelationship) -> bool:
        key = self._get_key(relationship.agent_a, relationship.agent_b)
        try:
            await self.redis.set(key, relationship.to_dict())
            return True
        except Exception as e:
            logger.error(f"Error saving relationship: {e}")
            return False

    async def delete(self, agent_a: str, agent_b: str) -> bool:
        key = self._get_key(agent_a, agent_b)
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting relationship: {e}")
            return False

    async def get_all_for_agent(self, agent_id: str) -> list[AgentRelationship]:
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
                    relationships.append(AgentRelationship.from_dict(data))
        except Exception as e:
            logger.error(f"Error getting relationships for agent: {e}")
        return relationships
