import asyncio
import datetime
import json
import logging
import os
import sys
import time
from typing import Any, List, Optional
from uuid import uuid4

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger("H-CORE")


class RedisLogHandler(logging.Handler):
    """Broadcasts logs to Redis for UI visibility."""

    def __init__(self, redis_client):
        super().__init__()
        self.redis = redis_client
        self._is_emitting = False

    def emit(self, record):
        if record.levelno < self.level:
            return
        if self._is_emitting:
            return
        try:
            self._is_emitting = True
            msg_str = self.format(record)
            data = {
                "type": "system.log",
                "sender": {"agent_id": "core", "role": "system"},
                "payload": {"content": msg_str},
            }
            asyncio.create_task(self.redis.publish_event("system_stream", data))
        except Exception:
            pass
        finally:
            self._is_emitting = False


class HaremOrchestrator:
    def __init__(self):
        try:
            from src.infrastructure.redis import RedisClient
            from src.infrastructure.surrealdb import SurrealDbClient
            from src.infrastructure.llm import LlmClient
            from src.infrastructure.plugin_loader import AgentRegistry
            from src.features.home.social_arbiter.arbiter import SocialArbiter
            from src.services.visual.service import VisualImaginationService
            from src.services.visual.manager import AssetManager
            from src.services.visual.provider import NanoBananaProvider
            from src.services.chat.commands import CommandHandler
            from src.domain.memory import MemoryConsolidator
            from src.services.proactivity.engine import ProactivityEngine
            from src.infrastructure.ha_client import HaClient
            from src.services.ha_event_worker import HaEventWorker

            self.RedisClient = RedisClient
            self.SurrealDbClient = SurrealDbClient
            self.LlmClient = LlmClient
            self.AgentRegistry = AgentRegistry
            self.SocialArbiter = SocialArbiter
            self.VisualImaginationService = VisualImaginationService
            self.AssetManager = AssetManager
            self.NanoBananaProvider = NanoBananaProvider
            self.CommandHandler = CommandHandler
            self.MemoryConsolidator = MemoryConsolidator
            self.ProactivityEngine = ProactivityEngine
            self.HaClient = HaClient
            self.HaEventWorker = HaEventWorker
        except ImportError as e:
            logger.error(f"INIT: Import error: {e}")
            raise e

        self.redis = self.RedisClient(host=os.getenv("REDIS_HOST", "redis"))
        self.surreal = self.SurrealDbClient(
            url=os.getenv("SURREALDB_URL", "ws://surrealdb:8000/rpc"),
            user=os.getenv("SURREALDB_USER", "root"),
            password=os.getenv("SURREALDB_PASS", "root"),
        )
        self.llm = self.LlmClient()

        # System LLM for social arbiter (immutable defaults)
        self.system_llm = self.LlmClient()
        self.agent_registry = self.AgentRegistry()
        self.social_arbiter = self.SocialArbiter(llm_client=self.system_llm)

        self.stop_event = asyncio.Event()
        self.tasks = []
        self.discussion_budget = 0
        self.MAX_DISCUSSION_BUDGET = 5

    async def status_heartbeat(self):
        logger.info("💓 HEARTBEAT: Consolidated worker started.")
        while not self.stop_event.is_set():
            try:
                # 1. Component Health
                health = {"redis": "offline", "llm": "offline", "brain": "offline"}

                # Check Redis
                if self.redis.client:
                    try:
                        await self.redis.client.ping()
                        health["redis"] = "ok"
                    except:
                        pass

                # Check Brain (SurrealDB)
                if self.surreal.client:
                    try:
                        # Simple query to check if session is active
                        res = await self.surreal._call("query", "INFO FOR DB;")
                        if res:
                            # In some library versions it's a list, in others a dict
                            # If we get ANY non-empty response, it's alive
                            health["brain"] = "ok"
                    except:
                        pass

                # Check LLM
                from src.infrastructure.llm import LITELLM_AVAILABLE

                if LITELLM_AVAILABLE:
                    # For now, if LiteLLM is loaded, we consider it "ready"
                    # A more thorough check would involve a micro-request
                    health["llm"] = "ok"

                # 2. Agent Stats
                agents_stats = {}
                for aid, agent in list(self.agent_registry.agents.items()):
                    loc = "Unknown"
                    if self.surreal.client:
                        try:
                            states = await self.surreal.get_agent_state(aid)
                            for s in states:
                                if s.get("relation") == "IS_IN":
                                    loc = s.get("name", "Unknown")
                        except:
                            pass

                    agents_stats[aid] = {
                        "status": "idle" if agent.is_active else "disabled",
                        "active": agent.is_active,
                        "llm_model": agent.llm.model,
                        "prompt_tokens": agent.ctx.prompt_tokens,
                        "completion_tokens": agent.ctx.completion_tokens,
                        "total_tokens": agent.ctx.total_tokens,
                        "cost": agent.ctx.total_tokens * 0.00002,
                        "location": loc,
                        "preferred_location": getattr(agent.config, "preferred_location", "None"),
                        "skills": [{"name": n, "active": True} for n in agent.tools.keys()],
                    }

                # 3. Broadcast Bundle
                heartbeat = {
                    "type": "system.heartbeat",
                    "sender": {"agent_id": "core", "role": "system"},
                    "payload": {"content": {"health": health, "agents": agents_stats}},
                }
                await self.redis.publish_event("system_stream", heartbeat)
            except Exception as e:
                logger.error(f"HEARTBEAT_FAIL: {e}")
            await asyncio.sleep(5)

    async def handle_message(self, data: dict):
        from src.models.hlink import HLinkMessage

        try:
            msg_type = data.get("type")
            # Skip logs and noise immediately
            if not msg_type or msg_type in ["system.log", "whisper_status", "system.heartbeat"]:
                return

            logger.error(f"📩 ORCHESTRATOR: Processing {msg_type}")
            msg, error = HLinkMessage.validate_message(data)
            if error:
                logger.error(f"❌ VALIDATION ERROR: {error}")
                return

            if msg.sender.role == "user":
                self.discussion_budget = self.MAX_DISCUSSION_BUDGET
                if hasattr(self, "sleep_scheduler"):
                    self.sleep_scheduler.record_activity()

            # Handle Config Updates
            if msg_type == "system.config_update":
                new_cfg = msg.payload.content.get("llm_config")
                if new_cfg:
                    logger.error(f"⚙️ CORE: Saving global config override...")
                    await self.surreal.save_config("system", {"llm_config": new_cfg})
                    # Refresh all agents
                    for agent in self.agent_registry.agents.values():
                        asyncio.create_task(agent.refresh_config())
                return

            if msg_type == "agent.config_update":
                agent_id = msg.payload.content.get("agent_id")
                new_cfg = msg.payload.content.get("llm_config")
                is_active = msg.payload.content.get("active")

                if agent_id:
                    # Handle LLM Config
                    if new_cfg:
                        logger.error(f"⚙️ CORE: Saving override for {agent_id}...")
                        await self.surreal.save_config(f"agent_{agent_id}", new_cfg)

                    # Handle Active Status
                    agent = self.agent_registry.agents.get(agent_id)
                    if agent:
                        if is_active is not None:
                            agent.is_active = is_active
                            logger.error(f"⚙️ CORE: Agent {agent_id} set to active={is_active}")

                        # Always refresh to apply potential LLM changes
                        asyncio.create_task(agent.refresh_config())
                return

            target = msg.recipient.target
            content = str(msg.payload.content)

            if target == "user":
                # logger.error(f"👤 UI MESSAGE: Ignoring agent response to user")
                return

            logger.error(f"🎯 TARGET: {target} | CONTENT: {content[:50]}")

            if target == "broadcast" or target == "all":
                logger.error("👥 Calling SocialArbiter...")
                responders = await self.social_arbiter.determine_responder_async(content)
                logger.error(f"👥 ARBITER: Found {len(responders) if responders else 0} responders")
                if responders:
                    for p in responders:
                        logger.error(f"📢 PUBLISHING to agent:{p.agent_id}")
                        await self.redis.publish(f"agent:{p.agent_id}", msg)
            elif target in self.agent_registry.agents:
                logger.error(f"📢 Direct PUBLISHING to agent:{target}")
                await self.redis.publish(f"agent:{target}", msg)

            if msg.sender.role != "user" and self.discussion_budget > 0:
                self.discussion_budget -= 1
                responders = await self.social_arbiter.determine_responder_async(content)
                if responders:
                    for p in responders:
                        if p.agent_id != msg.sender.agent_id:
                            await self.redis.publish(f"agent:{p.agent_id}", msg)
        except Exception as e:
            logger.error(f"🔥 ROUTER ERROR: {e}")

    async def message_router(self):
        logger.error("📡 ROUTER: Worker started.")

        async def handler_with_log(data):
            # logger.error(f"!!! HANDLER CALLED WITH: {data.get('type')}")
            await self.handle_message(data)

        # Restore standard stable listeners
        asyncio.create_task(self.redis.listen_stream("system_stream", "h-core-sys", "core-1", handler_with_log))
        asyncio.create_task(self.redis.listen_stream("conversation_stream", "h-core-conv", "core-1", handler_with_log))

        while not self.stop_event.is_set():
            await asyncio.sleep(1)

    async def _background_setup(self):
        logger.info("⚙️ SETUP: Starting...")
        try:
            await self.surreal.connect()
            asset_mgr = self.AssetManager(self.surreal)
            self.visual_service = self.VisualImaginationService(
                self.NanoBananaProvider(), asset_mgr, self.llm, self.redis
            )
            self.command_handler = self.CommandHandler(self.redis, self.visual_service, self.surreal)
            self.consolidator = self.MemoryConsolidator(self.surreal, self.llm, self.redis)
            self.proactivity_engine = self.ProactivityEngine(self.redis, self.surreal)

            from src.services.sleep_scheduler import SleepScheduler

            self.sleep_scheduler = SleepScheduler(self.consolidator, self.redis)
            self.command_handler.set_sleep_callback(self.sleep_scheduler.force_run)
            asyncio.create_task(self.sleep_scheduler.run_loop())
            logger.info("⚙️ SETUP: SleepScheduler started.")

            from src.services.media_cleanup import MediaCleanupWorker

            media_path = os.getenv("MEDIA_STORAGE_PATH", "/media/generated")
            self.media_cleanup = MediaCleanupWorker(
                storage_path=media_path,
                surreal_client=self.surreal,
                max_files=int(os.getenv("MEDIA_MAX_FILES", "200")),
            )
            asyncio.create_task(self.media_cleanup.run_loop())
            logger.info("⚙️ SETUP: MediaCleanupWorker started.")

            from src.infrastructure.plugin_loader import PluginLoader

            self.plugin_loader = PluginLoader(
                os.getenv("AGENTS_PATH", "/app/agents"),
                self.agent_registry,
                self.redis,
                self.llm,
                self.surreal,
                self.visual_service,
                None,
            )
            await self.plugin_loader.start()

            for agent in self.agent_registry.agents.values():
                from src.features.home.social_arbiter.models import AgentProfile

                p = AgentProfile(
                    agent_id=agent.config.name,
                    name=agent.config.name,
                    role=agent.config.role,
                    domains=agent.config.capabilities,
                    is_active=agent.is_active,
                )
                self.social_arbiter.register_agent(p)
                # Pass social arbiter to agent for stats tracking
                agent.social = self.social_arbiter
                asyncio.create_task(self.consolidator.generate_backstory(agent.config.name, agent.config.role))
            logger.info("⚙️ SETUP: Completed.")
        except Exception as e:
            logger.error(f"SETUP_ERR: {e}")

    async def run(self):
        logger.error("🚀 BOOTING...")
        if not await self.redis.connect():
            logger.error("❌ REDIS CONNECTION FAILED")
            return

        logger.error("✅ REDIS CONNECTED")

        # STORY 14.1 FIX: Disable Redis logging for h-core to avoid recursion loops
        # log_handler = RedisLogHandler(self.redis)
        # log_handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
        # logging.getLogger().addHandler(log_handler)

        self.tasks = [
            asyncio.create_task(self.status_heartbeat()),
            asyncio.create_task(self.message_router()),
            asyncio.create_task(self._background_setup()),
        ]

        logger.error(f"🚀 TASKS CREATED: {len(self.tasks)}")
        await asyncio.gather(*self.tasks, return_exceptions=True)


if __name__ == "__main__":
    orch = HaremOrchestrator()
    try:
        asyncio.run(orch.run())
    except KeyboardInterrupt:
        pass
