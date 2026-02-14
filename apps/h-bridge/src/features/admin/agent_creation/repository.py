import logging
from typing import Any

from src.features.admin.agent_creation.models import AgentCreationPayload

logger = logging.getLogger(__name__)


class AgentCreationRepository:
    TABLE_NAME = "agents"

    def __init__(self, surreal_client):
        self.surreal = surreal_client

    async def save(self, payload: AgentCreationPayload) -> AgentCreationPayload:
        data = payload.model_dump()
        data["version"] = "1.0.0"
        
        await self.surreal._call("create", self.TABLE_NAME, data)
        logger.info(f"AgentCreationRepository: Saved agent {payload.name}")
        return payload

    async def get_by_name(self, name: str) -> AgentCreationPayload | None:
        try:
            result = await self.surreal._call(
                "query",
                f"SELECT * FROM {self.TABLE_NAME} WHERE name = $name LIMIT 1;",
                {"name": name}
            )
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                if records and len(records) > 0:
                    record = records[0]
                    return AgentCreationPayload.model_validate(record)
        except Exception as e:
            logger.error(f"AgentCreationRepository: Failed to get agent {name}: {e}")
        return None

    async def delete(self, name: str) -> bool:
        try:
            await self.surreal._call(
                "query",
                f"DELETE FROM {self.TABLE_NAME} WHERE name = $name;",
                {"name": name}
            )
            logger.info(f"AgentCreationRepository: Deleted agent {name}")
            return True
        except Exception as e:
            logger.error(f"AgentCreationRepository: Failed to delete agent {name}: {e}")
            return False

    async def list_all(self) -> list[dict[str, Any]]:
        try:
            result = await self.surreal._call("query", f"SELECT * FROM {self.TABLE_NAME};")
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                return records
        except Exception as e:
            logger.error(f"AgentCreationRepository: Failed to list agents: {e}")
        return []

    async def get_enabled_agents(self) -> list[AgentCreationPayload]:
        try:
            result = await self.surreal._call(
                "query",
                f"SELECT * FROM {self.TABLE_NAME} WHERE enabled = true;"
            )
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                return [AgentCreationPayload.model_validate(r) for r in records]
        except Exception as e:
            logger.error(f"AgentCreationRepository: Failed to get enabled agents: {e}")
        return []
