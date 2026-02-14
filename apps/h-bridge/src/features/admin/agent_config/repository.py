import logging
from typing import Any

from src.features.admin.agent_config.models import AgentConfigSchema, AgentParameters, DEFAULT_PARAMETERS

logger = logging.getLogger(__name__)


class AgentConfigRepository:
    TABLE_NAME = "agent_config"

    def __init__(self, surreal_client):
        self.surreal = surreal_client

    async def save(self, agent_id: str, parameters: AgentParameters) -> AgentConfigSchema:
        data = {
            "agent_id": agent_id,
            "parameters": parameters.to_dict(),
            "enabled": True,
            "version": "1.0.0"
        }

        existing = await self.get(agent_id)
        if existing:
            await self.surreal._call(
                "query",
                f"UPDATE {self.TABLE_NAME} SET parameters = $params, version = '1.0.0' WHERE agent_id = $agent_id;",
                {"params": parameters.to_dict(), "agent_id": agent_id}
            )
        else:
            await self.surreal._call("create", self.TABLE_NAME, data)

        logger.info(f"AgentConfigRepository: Saved config for agent {agent_id}")
        return AgentConfigSchema(agent_id=agent_id, parameters=parameters, enabled=True)

    async def get(self, agent_id: str) -> AgentConfigSchema | None:
        try:
            result = await self.surreal._call(
                "query",
                f"SELECT * FROM {self.TABLE_NAME} WHERE agent_id = $agent_id LIMIT 1;",
                {"agent_id": agent_id}
            )
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                if records and len(records) > 0:
                    record = records[0]
                    return AgentConfigSchema(
                        agent_id=record.get("agent_id", agent_id),
                        parameters=AgentParameters.from_dict(record.get("parameters", {})),
                        enabled=record.get("enabled", True),
                        version=record.get("version", "1.0.0")
                    )
        except Exception as e:
            logger.error(f"AgentConfigRepository: Failed to get config for {agent_id}: {e}")
        return None

    async def delete(self, agent_id: str) -> bool:
        try:
            await self.surreal._call(
                "query",
                f"DELETE FROM {self.TABLE_NAME} WHERE agent_id = $agent_id;",
                {"agent_id": agent_id}
            )
            logger.info(f"AgentConfigRepository: Deleted config for agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"AgentConfigRepository: Failed to delete config for {agent_id}: {e}")
            return False

    async def list_all(self) -> list[AgentConfigSchema]:
        try:
            result = await self.surreal._call("query", f"SELECT * FROM {self.TABLE_NAME};")
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                return [
                    AgentConfigSchema(
                        agent_id=r.get("agent_id"),
                        parameters=AgentParameters.from_dict(r.get("parameters", {})),
                        enabled=r.get("enabled", True),
                        version=r.get("version", "1.0.0")
                    )
                    for r in records
                ]
        except Exception as e:
            logger.error(f"AgentConfigRepository: Failed to list configs: {e}")
        return []

    async def get_or_default(self, agent_id: str) -> AgentParameters:
        config = await self.get(agent_id)
        if config:
            return config.parameters
        return DEFAULT_PARAMETERS
