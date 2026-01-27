import asyncio
import logging
import os
from typing import Any

from src.domain.memory import MemoryConsolidator
from src.infrastructure.llm import LlmClient
from src.infrastructure.plugin_loader import AgentRegistry, PluginLoader
from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender
from src.utils.privacy import PrivacyFilter

# Logging setup
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("H-CORE")

# Global privacy filter
privacy_filter = PrivacyFilter()

# Global consolidator
consolidator = None

class RedisLogHandler(logging.Handler):
    """Custom logging handler that publishes logs to Redis as SYSTEM_LOG messages."""
    def __init__(self, redis_client):
        super().__init__()
        self.redis_client = redis_client
        self.ignored_loggers = ["src.infrastructure.redis", "uvicorn", "fastapi", "asyncio", "aiosqlite"]
        self.level_map = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    def set_level(self, level: str):
        if level.upper() in self.level_map:
            self.log_level = level.upper()

    def emit(self, record):
        if any(ignored in record.name for ignored in self.ignored_loggers):
            return
            
        current_level = self.level_map.get(record.levelname, 20)
        min_level = self.level_map.get(self.log_level, 20)
        
        if current_level < min_level:
            return

        log_entry = self.format(record)
        redacted_log, _ = privacy_filter.redact(log_entry)
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._publish_log(redacted_log, record.levelname))
        except RuntimeError:
            pass 

    async def _publish_log(self, content, level):
        msg = HLinkMessage(
            type=MessageType.SYSTEM_LOG,
            sender=Sender(agent_id="system", role="orchestrator"),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content=f"[{level}] {content}")
        )
        await self.redis_client.publish("broadcast", msg)

# Infrastructure Clients
redis_client = RedisClient(host=os.getenv("REDIS_HOST", "localhost"))
surreal_client = SurrealDbClient(
    url=os.getenv("SURREALDB_URL", "ws://surrealdb:8000/rpc"),
    user=os.getenv("SURREALDB_USER", "root"),
    password=os.getenv("SURREALDB_PASS", "root")
)
llm_client = LlmClient()
agent_registry = AgentRegistry()
plugin_loader = PluginLoader(os.getenv("AGENTS_PATH", "/app/agents"), agent_registry, redis_client, llm_client, surreal_client)

log_handler = None

async def health_check_loop():
    """Periodically checks backend services and broadcasts status."""
    while True:
        try:
            redis_status = "ok" if redis_client.client and await redis_client.client.ping() else "error"
            llm_status = "ok"
            
            if redis_client.client: 
                await redis_client.publish(
                    "broadcast",
                    HLinkMessage(
                        type=MessageType.SYSTEM_STATUS_UPDATE,
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target="system"),
                        payload=Payload(content={"component": "redis", "status": redis_status})
                    )
                )
                
                await redis_client.publish(
                    "broadcast",
                    HLinkMessage(
                        type=MessageType.SYSTEM_STATUS_UPDATE,
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target="system"),
                        payload=Payload(content={"component": "llm", "status": llm_status})
                    )
                )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        await asyncio.sleep(30)

async def heartbeat_loop():
    """Periodically publishes a heartbeat to Redis."""
    logger.info("HEARTBEAT: Loop started.")
    while True:
        try:
            msg = HLinkMessage(
                type=MessageType.SYSTEM_STATUS_UPDATE,
                sender=Sender(agent_id="core", role="system"),
                recipient=Recipient(target="system"),
                payload=Payload(content={"component": "brain", "status": "online"})
            )
            await redis_client.publish("broadcast", msg)
        except Exception as e:
            logger.error(f"HEARTBEAT: Error: {e}")
        await asyncio.sleep(10)

async def sleep_cycle_loop():
    """Periodically runs memory consolidation."""
    global consolidator
    interval = float(os.getenv("SLEEP_CYCLE_INTERVAL", "3600"))
    logger.info(f"SLEEP_CYCLE: Background loop started. Interval: {interval}s")
    
    while True:
        try:
            await asyncio.sleep(interval)
            if consolidator:
                logger.info("SLEEP_CYCLE: Starting consolidation...")
                await consolidator.consolidate()
                await consolidator.apply_decay()
        except Exception as e:
            logger.error(f"SLEEP_CYCLE: Loop error: {e}")

async def persistence_worker():
    """Listens to all narrative messages and persists them to SurrealDB."""
    logger.info("PERSISTENCE: Worker started.")
    
    async def handler(msg: HLinkMessage):
        if msg.type in [MessageType.NARRATIVE_TEXT, MessageType.EXPERT_RESPONSE]:
            msg_data = msg.model_dump()
            # Redact secrets before storage
            if isinstance(msg_data.get("payload", {}).get("content"), str):
                redacted_text, _ = privacy_filter.redact(msg_data["payload"]["content"])
                msg_data["payload"]["content"] = redacted_text
            
            await surreal_client.persist_message(msg_data)

    await redis_client.subscribe("broadcast", handler)

async def config_update_worker():
    """Listens for system config updates."""
    logger.info("SYSTEM: Config update worker started.")
    async def handler(msg: Any):
        # Handle raw dict if bridge sends it directly or HLinkMessage
        data = msg.payload.content if hasattr(msg, 'payload') else msg.get('content', {})
        if not isinstance(data, dict):
            return
            
        log_level = data.get("log_level")
        if log_level and log_handler:
            log_handler.set_level(log_level)
            logger.info(f"SYSTEM: Log level updated to {log_level}")

    await redis_client.subscribe("broadcast", handler)

async def main():
    global consolidator, log_handler
    logger.info("H-Core Daemon starting...")
    
    # Connect infrastructure
    await redis_client.connect()
    await surreal_client.connect()
    
    # Register Redis log handler
    log_handler = RedisLogHandler(redis_client)
    logging.getLogger().addHandler(log_handler)
    
    # Initialize Consolidator
    consolidator = MemoryConsolidator(surreal_client, llm_client, redis_client)
    
    # Start agents
    await plugin_loader.start()
    
    # Run loops
    await asyncio.gather(
        health_check_loop(),
        sleep_cycle_loop(),
        persistence_worker(),
        heartbeat_loop(),
        config_update_worker()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("H-Core Daemon stopped by user.")
    except Exception as e:
        logger.critical(f"H-Core Daemon crashed: {e}", exc_info=True)
