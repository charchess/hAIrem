import logging
from typing import Any

logger = logging.getLogger(__name__)


class AdminCommandHandler:
    def __init__(self, agent_registry, skill_mgmt_service, redis_client):
        self.registry = agent_registry
        self.skill_mgmt = skill_mgmt_service
        self.redis = redis_client

    async def handle(self, msg_type: str, payload: dict) -> bool:
        if msg_type == "admin.skill.list":
            await self._handle_skill_list()
            return True

        if msg_type == "admin.skill.grant":
            persona_id = payload.get("persona_id")
            skill_name = payload.get("skill_name")
            if not persona_id or not skill_name:
                await self._publish(
                    "admin.skill.grant.response", {"success": False, "error": "persona_id and skill_name required"}
                )
                return True
            result = await self.skill_mgmt.grant(persona_id, skill_name)
            await self._publish("admin.skill.grant.response", result)
            return True

        if msg_type == "admin.skill.revoke":
            persona_id = payload.get("persona_id")
            skill_name = payload.get("skill_name")
            if not persona_id or not skill_name:
                await self._publish(
                    "admin.skill.revoke.response", {"success": False, "error": "persona_id and skill_name required"}
                )
                return True
            result = await self.skill_mgmt.revoke(persona_id, skill_name)
            await self._publish("admin.skill.revoke.response", result)
            return True

        if msg_type == "admin.agent.list":
            await self._handle_agent_list()
            return True

        return False

    async def _handle_skill_list(self):
        try:
            skills = await self.skill_mgmt.list_skills()
            await self._publish("admin.skill.list.response", {"success": True, "skills": skills})
        except Exception as e:
            logger.error(f"ADMIN: skill.list failed: {e}")
            await self._publish("admin.skill.list.response", {"success": False, "error": str(e)})

    async def _handle_agent_list(self):
        try:
            agents = []
            for agent_id, agent in self.registry.agents.items():
                agents.append(
                    {
                        "agent_id": agent_id,
                        "role": agent.config.role,
                        "is_active": agent.is_active,
                        "personified": getattr(agent, "personified", True),
                        "skills": [
                            {"name": n, "skill_package": v.get("skill_package"), "active": True}
                            for n, v in agent.tools.items()
                        ],
                    }
                )
            await self._publish("admin.agent.list.response", {"success": True, "agents": agents})
        except Exception as e:
            logger.error(f"ADMIN: agent.list failed: {e}")
            await self._publish("admin.agent.list.response", {"success": False, "error": str(e)})

    async def _publish(self, response_type: str, content: Any):
        event = {
            "type": response_type,
            "sender": {"agent_id": "core", "role": "system"},
            "payload": {"content": content},
        }
        await self.redis.publish_event("system_stream", event)
