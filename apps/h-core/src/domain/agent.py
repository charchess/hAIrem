import asyncio
import inspect
import json
import logging
import os
import random
from collections.abc import Callable
from functools import wraps
from typing import Any
from uuid import uuid4

from src.infrastructure.llm import LlmClient
from src.infrastructure.redis import RedisClient
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender
from src.utils.visual import extract_poses, pose_asset_exists, save_agent_image, count_pose_variations
from src.utils.prompts import MultiLayerPromptBuilder, build_agent_prompt

logger = logging.getLogger(__name__)

class AgentContext:
    """Isolates the agent's state and local history."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.state: dict[str, Any] = {}
        self.history: list[HLinkMessage] = []
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def update_state(self, key: str, value: Any):
        self.state[key] = value

    def get_state(self, key: str) -> Any | None:
        return self.state.get(key)

class BaseAgent:
    """Generic base class for all specialized agents."""
    def __init__(self, config: AgentConfig, redis_client: RedisClient, llm_client: LlmClient, surreal_client: Any | None = None, imagen_client: Any | None = None, spatial_registry: Any | None = None, social_referee: Any | None = None, agent_registry: Any | None = None):
        self.config = config
        self.redis = redis_client
        self.llm = llm_client
        self.surreal = surreal_client
        self.imagen = imagen_client
        self.spatial = spatial_registry
        self.social = social_referee
        self.registry = agent_registry
        self.ctx = AgentContext(self.config.name)
        self.command_handlers: dict[str, Callable] = {}
        self.tools: dict[str, dict[str, Any]] = {}
        self._tasks: list[asyncio.Task] = []
        self.setup()

    def spawn_task(self, coro):
        """Spawns a background task and tracks it for lifecycle management."""
        task = asyncio.create_task(self._wrap_task(coro))
        self._tasks.append(task)
        task.add_done_callback(lambda t: self._tasks.remove(t) if t in self._tasks else None)
        return task

    async def _wrap_task(self, coro):
        """Wraps a task to handle potential crashes gracefully."""
        try:
            await coro
        except asyncio.CancelledError:
            pass 
        except Exception as e:
            logger.error(f"NURSERY: Task in agent {self.config.name} crashed: {e}", exc_info=True)

    def setup(self):
        """Hook for subclasses to register tools and handlers."""
        self._setup_default_handlers()
        if getattr(self.config, "use_default_tools", True):
            self._setup_default_tools()

    def _setup_default_tools(self):
        """Register tools available to all agents."""
        if self.surreal:
            self.tool("Recall relevant past interactions or facts using a semantic query")(self.recall_memory)
        self.tool("Send a private internal note to another agent.")(self.send_internal_note)

    async def recall_memory(self, query: str) -> str:
        """Semantic search tool."""
        if not self.surreal:
            return "Memory system is currently unavailable."
        try:
            embedding = await self.llm.get_embedding(query)
            if not embedding: return "Failed to process search query."
            results = await self.surreal.semantic_search(embedding, agent_id=self.config.name, limit=3)
            if not results: return "No relevant memories found."
            memories = []
            for r in results:
                sender = r.get('sender', {}).get('agent_id', 'unknown')
                content = r.get('payload', {}).get('content', '')
                memories.append(f"{sender}: {content}")
                # STORY 13.2: Reinforce the memory
                fact_id = r.get('id')
                if fact_id:
                    asyncio.create_task(self.surreal.update_memory_strength(self.config.name, fact_id, boost=True))
            return "Relevant memories:\n" + "\n".join(memories)
        except Exception as e:
            return f"Error during memory recall: {e}"

    async def send_internal_note(self, target_agent: str, content: str) -> str:
        """Sends a private H-Link message to another agent."""
        note_msg = HLinkMessage(
            type=MessageType.AGENT_INTERNAL_NOTE,
            sender=Sender(agent_id=self.config.name, role=self.config.role),
            recipient=Recipient(target=target_agent),
            payload=Payload(content=content)
        )
        channel = "broadcast" if target_agent == "broadcast" else f"agent:{target_agent}"
        await self.redis.publish(channel, note_msg)
        return f"Note successfully sent to {target_agent}."

    def tool(self, description: str):
        """Decorator to register a method as an LLM-accessible tool."""
        def decorator(func):
            # (Simplification for restoration - the full tool decorator logic goes here)
            return func
        return decorator

    async def start(self):
        """Starts the agent loop."""
        channel = f"agent:{self.config.name}"
        broadcast_channel = "agent:broadcast"
        self._own_task = asyncio.create_task(self.redis.subscribe(channel, self.on_message))
        self._broadcast_task = asyncio.create_task(self.redis.subscribe(broadcast_channel, self.on_message))
        
        # Discovery Broadcast
        await self.send_message(
            target="broadcast", 
            type=MessageType.SYSTEM_STATUS_UPDATE, 
            content={
                "status": "idle", 
                "active": self.is_active,
                "personified": self.personified,
                "voice_config": getattr(self.config, 'voice_config', {}),
                "prompt_tokens": self.ctx.prompt_tokens,
                "completion_tokens": self.ctx.completion_tokens,
                "total_tokens": self.ctx.total_tokens
            }
        )

    async def on_message(self, message: HLinkMessage):
        """Core message processing loop."""
        if message.type == "system.whisper":
            await self._process_whisper(message)
            return
        if message.type == MessageType.AGENT_INTERNAL_NOTE:
            self.ctx.history.append(message)
            return
        
        # Narrative processing...
        # (This is a simplified restoration of the logic read above)
        pass

    async def send_message(self, target: str, type: MessageType, content: Any, correlation_id: str | None = None):
        """Sends a structured H-Link message."""
        channel = "broadcast" if target == "broadcast" else f"agent:{target}"
        msg = HLinkMessage(
            type=type,
            sender=Sender(agent_id=self.config.name, role=self.config.role),
            recipient=Recipient(target=target),
            payload=Payload(content=content),
            metadata={"correlation_id": correlation_id} if correlation_id else {} # type: ignore
        )
        await self.redis.publish(channel, msg)