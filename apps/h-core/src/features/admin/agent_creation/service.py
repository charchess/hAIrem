import logging
from typing import Any

from src.features.admin.agent_creation.models import AgentCreationPayload
from src.features.admin.agent_creation.repository import AgentCreationRepository

logger = logging.getLogger(__name__)


class AgentCreationService:
    def __init__(self, surreal_client, plugin_loader=None, agent_registry=None, room_service=None):
        self.repository = AgentCreationRepository(surreal_client)
        self.plugin_loader = plugin_loader
        self.agent_registry = agent_registry
        self.room_service = room_service

    async def create_agent(self, payload: AgentCreationPayload) -> dict[str, Any]:
        try:
            existing = await self.repository.get_by_name(payload.name)
            if existing:
                return {"success": False, "error": f"Agent '{payload.name}' already exists"}

            await self.repository.save(payload)
            
            if self.plugin_loader and payload.agents_folder:
                await self.plugin_loader.load_agent_from_folder(payload.agents_folder)
            elif self.plugin_loader and payload.name:
                folder_path = await self._create_agent_folder(payload)
                if folder_path:
                    await self.plugin_loader.load_agent_from_folder(folder_path)
            
            return {
                "success": True,
                "agent_id": payload.name,
                "message": f"Agent '{payload.name}' created successfully"
            }
        except Exception as e:
            logger.error(f"AgentCreationService: Failed to create agent: {e}")
            return {"success": False, "error": str(e)}

    async def _create_agent_folder(self, payload: AgentCreationPayload) -> str | None:
        if not self.plugin_loader:
            return None
        manifest_dict = payload.to_manifest_dict()
        return await self.plugin_loader.create_agent_folder(manifest_dict)

    async def list_agents_from_db(self) -> list[dict[str, Any]]:
        agents = await self.repository.list_all()
        
        if self.room_service:
            for agent in agents:
                agent_name = agent.get("name")
                if agent_name:
                    room_info = await self.room_service.get_agent_room(agent_name)
                    agent["room"] = room_info
        
        return agents

    async def get_agent(self, agent_id: str) -> dict[str, Any]:
        agent = await self.repository.get_by_name(agent_id)
        if not agent:
            return {"success": False, "error": f"Agent '{agent_id}' not found"}
        return {"success": True, "agent": agent.model_dump()}

    async def delete_agent(self, agent_id: str) -> dict[str, Any]:
        try:
            await self.repository.delete(agent_id)
            if self.agent_registry and agent_id in self.agent_registry.agents:
                agent = self.agent_registry.agents[agent_id]
                if hasattr(agent, 'stop'):
                    await agent.stop()
                del self.agent_registry.agents[agent_id]
            return {"success": True, "message": f"Agent '{agent_id}' deleted"}
        except Exception as e:
            logger.error(f"AgentCreationService: Failed to delete agent: {e}")
            return {"success": False, "error": str(e)}
