from typing import Any

# STORY 5.6: HaClient migrated to Electra drivers
from agents.electra.drivers.ha_client import HaClient

from src.domain.agent import BaseAgent
from src.infrastructure.llm import LlmClient
from src.infrastructure.redis import RedisClient
from src.models.agent import AgentConfig


class ExpertDomotiqueAgent(BaseAgent):
    def __init__(self, config: AgentConfig, redis_client: RedisClient, llm_client: LlmClient, surreal_client: Any | None = None):
        super().__init__(config, redis_client, llm_client, surreal_client)
        self.ha_client = HaClient()
        
        # Registration des outils
        self.tool("Get the current state of a device (on/off, temperature, etc)")(self.get_entity_state)
        self.tool("Turn a device on or off (light, switch, etc)")(self.toggle_device)
        self.register_command("echo", self._handle_echo)
        self.register_command("ping", self._handle_ping)

    async def _handle_ping(self, payload: Any) -> str:
        return "Pong! Expert-Domotique est prêt."

    async def _handle_echo(self, payload: Any) -> str:
        text = payload.get("args", "Pas d'arguments") if isinstance(payload, dict) else "Echo"
        return f"Écho : {text}"

    async def get_entity_state(self, entity_id: str) -> str:
        state = await self.ha_client.get_state(entity_id)
        if state:
            return f"The state of {entity_id} is {state['state']}."
        return f"Could not find entity {entity_id}."

    async def toggle_device(self, entity_id: str, action: str = "toggle") -> str:
        """
        Action can be 'turn_on', 'turn_off', or 'toggle'.
        """
        domain = entity_id.split('.')[0]
        service = action if action in ["turn_on", "turn_off"] else "toggle"
        
        success = await self.ha_client.call_service(domain, service, {"entity_id": entity_id})
        if success:
            return f"Successfully executed {service} on {entity_id}."
        return f"Failed to execute command on {entity_id}."
