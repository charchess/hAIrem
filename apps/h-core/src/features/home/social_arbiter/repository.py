import logging
from typing import Any
from .models import AgentProfile, AgentEmotionalCapabilities
from src.infrastructure.surrealdb import SurrealDbClient

logger = logging.getLogger(__name__)


class AgentRepository:
    def __init__(self, surreal_client: SurrealDbClient | None = None):
        self.surreal = surreal_client

    async def load_all_agents(self) -> list[AgentProfile]:
        if not self.surreal or not self.surreal.client:
            logger.warning("SurrealDB client not available, returning empty agent list")
            return []

        try:
            result = await self.surreal._call("query", "SELECT * FROM agent WHERE is_active = true;")
            if not result or not isinstance(result, list) or len(result) == 0:
                return []

            data = result[0].get("result", []) if isinstance(result[0], dict) else result
            agents = []

            for row in data:
                agent = self._row_to_profile(row)
                if agent:
                    agents.append(agent)

            logger.info(f"Loaded {len(agents)} agents from SurrealDB")
            return agents

        except Exception as e:
            logger.error(f"Failed to load agents from SurrealDB: {e}")
            return []

    async def load_agent(self, agent_id: str) -> AgentProfile | None:
        if not self.surreal or not self.surreal.client:
            return None

        try:
            result = await self.surreal._call("query", f"SELECT * FROM agent WHERE id = agent:{agent_id};")
            if not result or not isinstance(result, list) or len(result) == 0:
                return None

            data = result[0].get("result", []) if isinstance(result[0], dict) else result
            if not data:
                return None

            return self._row_to_profile(data[0])

        except Exception as e:
            logger.error(f"Failed to load agent {agent_id} from SurrealDB: {e}")
            return None

    async def save_agent(self, agent: AgentProfile) -> bool:
        if not self.surreal or not self.surreal.client:
            return False

        try:
            data = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "description": agent.description,
                "interests": agent.interests,
                "domains": agent.domains,
                "expertise": agent.expertise,
                "personality_traits": agent.personality_traits,
                "is_active": agent.is_active,
                "priority_weight": agent.priority_weight,
            }

            if agent.emotional_capabilities:
                data["supported_emotions"] = agent.emotional_capabilities.supported_emotions
                data["emotional_range"] = agent.emotional_capabilities.emotional_range
                data["empathy_level"] = agent.emotional_capabilities.empathy_level
                data["adaptability"] = agent.emotional_capabilities.adaptability

            await self.surreal._call("create", f"agent:{agent.agent_id}", data)
            logger.info(f"Saved agent {agent.agent_id} to SurrealDB")
            return True

        except Exception as e:
            logger.error(f"Failed to save agent {agent.agent_id}: {e}")
            return False

    async def update_agent(self, agent: AgentProfile) -> bool:
        if not self.surreal or not self.surreal.client:
            return False

        try:
            data = {
                "name": agent.name,
                "role": agent.role,
                "description": agent.description,
                "interests": agent.interests,
                "domains": agent.domains,
                "expertise": agent.expertise,
                "personality_traits": agent.personality_traits,
                "is_active": agent.is_active,
                "priority_weight": agent.priority_weight,
            }

            if agent.emotional_capabilities:
                data["supported_emotions"] = agent.emotional_capabilities.supported_emotions
                data["emotional_range"] = agent.emotional_capabilities.emotional_range
                data["empathy_level"] = agent.emotional_capabilities.empathy_level
                data["adaptability"] = agent.emotional_capabilities.adaptability

            await self.surreal._call("query", f"UPDATE agent:{agent.agent_id} SET {', '.join(f'{k} = ${k}' for k in data.keys())};", data)
            logger.info(f"Updated agent {agent.agent_id} in SurrealDB")
            return True

        except Exception as e:
            logger.error(f"Failed to update agent {agent.agent_id}: {e}")
            return False

    def _row_to_profile(self, row: dict[str, Any]) -> AgentProfile | None:
        try:
            emotional_capabilities = AgentEmotionalCapabilities(
                supported_emotions=row.get("supported_emotions", []),
                emotional_range=row.get("emotional_range", []),
                empathy_level=row.get("empathy_level", 0.5),
                adaptability=row.get("adaptability", 0.5),
            )
            
            return AgentProfile(
                agent_id=row.get("agent_id", ""),
                name=row.get("name", ""),
                role=row.get("role", "standard"),
                description=row.get("description"),
                interests=row.get("interests", []),
                domains=row.get("domains", []),
                expertise=row.get("expertise", []),
                personality_traits=row.get("personality_traits", []),
                emotional_capabilities=emotional_capabilities,
                is_active=row.get("is_active", True),
                priority_weight=row.get("priority_weight", 1.0),
                last_response_time=row.get("last_response_time"),
                response_count=row.get("response_count", 0),
            )
        except Exception as e:
            logger.error(f"Failed to convert row to AgentProfile: {e}")
            return None
