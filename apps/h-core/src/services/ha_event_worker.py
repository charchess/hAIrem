import logging
import asyncio
from typing import Any, Dict
from src.infrastructure.redis import RedisClient
from src.infrastructure.ha_client import HaClient
from src.services.proactivity.engine import ProactivityEngine
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender

logger = logging.getLogger(__name__)


class HaEventWorker:
    def __init__(self, redis: RedisClient, ha_client: HaClient, proactivity_engine: ProactivityEngine = None):
        self.redis = redis
        self.ha_client = ha_client
        self.proactivity = proactivity_engine
        self.stop_event = asyncio.Event()
        self._task = None

    async def start(self):
        """Start listening to HA events and process them."""
        logger.info("HA_WORKER: Starting HA event listener...")

        # Launch listener loop in background
        self._task = asyncio.create_task(self.ha_client.listen_events(self.process_event))

        # Keep worker alive until stopped
        while not self.stop_event.is_set():
            await asyncio.sleep(1)

    async def process_event(self, event: Dict[str, Any]):
        """Process HA event, publish to Redis, and feed Proactivity Engine."""
        event_type = event.get("event_type", "unknown")
        data = event.get("data", {})

        # 1. Feed Proactivity Engine (Epic 10)
        if self.proactivity:
            # We normalize the event structure for the engine
            await self.proactivity.process_event(
                {
                    "type": "ha_event",
                    "name": event_type,
                    "entity_id": data.get("entity_id"),
                    "new_state": data.get("new_state", {}).get("state"),
                }
            )

        # 2. Legacy/Debug Broadcast (Epic 5)
        # Only broadcast significant state changes to avoid noise
        if event_type == "state_changed":
            entity_id = data.get("entity_id", "")
            new_state = data.get("new_state", {}).get("state")

            # Filter noise (optional, e.g. time sensors)
            if "sensor.time" in entity_id:
                return

            msg = HLinkMessage(
                type=MessageType.NARRATIVE_TEXT,
                sender=Sender(agent_id="ha_worker", role="system"),
                recipient=Recipient(target="broadcast"),
                payload=Payload(content=f"HA Event: {entity_id} changed to {new_state}"),
            )
            await self.redis.publish_event("system_stream", msg.model_dump(mode="json"))
            logger.debug(f"HA_WORKER: Processed event {event_type} for {entity_id}")

    async def stop(self):
        self.stop_event.set()
        if self._task:
            self._task.cancel()
        await self.ha_client.close()
        logger.info("HA_WORKER: Stopped.")
