from typing import Any


class AgentManagementService:
    def __init__(self, redis_client=None, agent_registry=None, arbiter_service=None):
        self.redis = redis_client
        # Handle both dict and object registry
        if isinstance(agent_registry, dict):
            self.agents = agent_registry
        else:
            self.agents = getattr(agent_registry, 'agents', {})
        self.arbiter_service = arbiter_service

    async def enable_agent(self, agent_id: str) -> dict[str, Any]:
        if agent_id not in self.agents:
            return {"success": False, "error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]
        # Handle both dict and object
        if isinstance(agent, dict):
            agent["is_active"] = True
        else:
            agent.is_active = True

        if self.arbiter_service:
            self.arbiter_service.set_agent_status(agent_id, True)

        await self._broadcast_status(agent_id, True)

        return {"success": True, "agent_id": agent_id, "is_active": True}

    async def disable_agent(self, agent_id: str) -> dict[str, Any]:
        if agent_id not in self.agents:
            return {"success": False, "error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]
        # Handle both dict and object
        if isinstance(agent, dict):
            agent["is_active"] = False
        else:
            agent.is_active = False

        if self.arbiter_service:
            self.arbiter_service.set_agent_status(agent_id, False)

        await self._broadcast_status(agent_id, False)

        return {"success": True, "agent_id": agent_id, "is_active": False}

    async def get_agent_status(self, agent_id: str) -> dict[str, Any]:
        if agent_id not in self.agents:
            return {"success": False, "error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]
        # Handle both dict and object
        if isinstance(agent, dict):
            return {
                "success": True,
                "agent_id": agent_id,
                "is_active": agent.get("is_active", True),
                "role": agent.get("role", "unknown"),
            }
        else:
            return {
                "success": True,
                "agent_id": agent_id,
                "is_active": agent.is_active,
                "role": agent.config.role,
            }

    async def list_agents(self) -> list[dict[str, Any]]:
        agents = []
        for agent_id, agent in self.agents.items():
            # Handle both dict and object
            if isinstance(agent, dict):
                agents.append({
                    "agent_id": agent_id,
                    "role": agent.get("role", "unknown"),
                    "is_active": agent.get("is_active", True),
                    "personified": agent.get("personified", True),
                })
            else:
                agents.append({
                    "agent_id": agent_id,
                    "role": agent.config.role,
                    "is_active": agent.is_active,
                    "personified": agent.personified,
                })
        return agents

    async def _broadcast_status(self, agent_id: str, is_active: bool):
        from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender
        
        status_msg = HLinkMessage(
            type=MessageType.SYSTEM_STATUS_UPDATE,
            sender=Sender(agent_id=agent_id, role="system"),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content={
                "status": "active" if is_active else "inactive",
                "active": is_active,
                "personified": True,
            })
        )
        
        if self.redis:
            await self.redis.publish_event("system_stream", status_msg.model_dump(mode='json'))
