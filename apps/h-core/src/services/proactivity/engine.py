import logging
from typing import Dict, List, Any
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

logger = logging.getLogger(__name__)


class ProactivityEngine:
    """
    Manages proactive behaviors, event triggers, and system stimuli (Epic 10).
    """

    def __init__(self, redis_client, surreal_client):
        self.redis = redis_client
        self.surreal = surreal_client
        self.triggers: List[Dict[str, Any]] = []
        self.stimuli: Dict[str, Dict[str, Any]] = {}

    async def register_trigger(
        self, event_name: str, target_agent: str, context: str = "", entity_id: str = None, new_state: str = None
    ):
        """
        Registers a complex trigger.
        """
        trigger = {
            "event_name": event_name,
            "entity_id": entity_id,
            "new_state": new_state,
            "target_agent": target_agent,
            "context": context or f"Event detected: {event_name}",
        }
        self.triggers.append(trigger)
        logger.info(f"PROACTIVITY: Registered trigger {event_name} ({entity_id}) -> {target_agent}")

    async def register_stimulus(self, stimulus_name: str, agent_ids: List[str], context: str = ""):
        """
        Registers a system stimulus.
        """
        self.stimuli[stimulus_name] = {"agents": agent_ids, "context": context or f"System Stimulus: {stimulus_name}"}
        logger.info(f"PROACTIVITY: Registered stimulus {stimulus_name} -> {agent_ids}")

    async def process_event(self, event_data: Dict[str, Any]):
        """
        FR53: Hardware Events.
        Matches event data against registered triggers.
        """
        event_name = event_data.get("name")
        entity_id = event_data.get("entity_id")
        new_state = event_data.get("new_state")

        logger.debug(f"PROACTIVITY: Evaluating event {event_name} for {entity_id} (state: {new_state})")

        for trigger in self.triggers:
            # Match Logic
            if trigger["event_name"] != event_name:
                continue

            if trigger["entity_id"] and trigger["entity_id"] != entity_id:
                continue

            if trigger["new_state"] and str(trigger["new_state"]) != str(new_state):
                continue

            # Match found!
            await self._trigger_agent(trigger["target_agent"], trigger["context"])

    async def trigger_stimulus(self, stimulus_name: str):
        """
        FR55: System Stimulus.
        """
        logger.info(f"PROACTIVITY: Firing stimulus {stimulus_name}")
        if stimulus_name in self.stimuli:
            cfg = self.stimuli[stimulus_name]
            for agent_id in cfg["agents"]:
                await self._trigger_agent(agent_id, cfg["context"])

    async def _trigger_agent(self, agent_id: str, context: str):
        """Sends a wakeup call to an agent."""
        msg = HLinkMessage(
            type=MessageType.SYSTEM_STATUS_UPDATE,  # Using status update as a "poke"
            sender=Sender(agent_id="core", role="system"),
            recipient=Recipient(target=agent_id),
            payload=Payload(content=f"PROACTIVE_TRIGGER: {context}"),
        )

        # Publish to agent's channel
        # Handle mock vs real redis
        try:
            res = self.redis.publish_event(f"agent:{agent_id}", msg.model_dump())
            if hasattr(res, "__await__"):
                await res
        except Exception:
            pass  # Ignore mock errors
