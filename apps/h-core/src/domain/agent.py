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
        self.current_user_id: str | None = None
        self.current_user_name: str | None = None

    def update_state(self, key: str, value: Any):
        self.state[key] = value

    def get_state(self, key: str) -> Any | None:
        return self.state.get(key)

    def set_user_context(self, user_id: str | None, user_name: str | None = None):
        """Set the current user context for memory filtering."""
        self.current_user_id = user_id
        self.current_user_name = user_name

    def get_user_context(self) -> tuple[str | None, str | None]:
        """Get the current user context."""
        return self.current_user_id, self.current_user_name

class BaseAgent:
    """Generic base class for all specialized agents."""
    def __init__(self, config: AgentConfig, redis_client: RedisClient, llm_client: LlmClient, surreal_client: Any | None = None, visual_service: Any | None = None, spatial_registry: Any | None = None, social_referee: Any | None = None, agent_registry: Any | None = None, token_tracking_service: Any | None = None):
        self.config = config
        self.redis = redis_client
        self.llm = llm_client
        self.surreal = surreal_client
        self.visual_service = visual_service
        self.spatial = spatial_registry
        self.social = social_referee
        self.registry = agent_registry
        self.token_tracking_service = token_tracking_service
        self.ctx = AgentContext(self.config.name)
        self.is_active = True
        self.personified = getattr(self.config, 'personified', True)
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
            
            user_id, user_name = self.ctx.get_user_context()
            
            if user_id:
                results = await self.surreal.semantic_search_user(embedding, user_id, limit=3)
            else:
                results = await self.surreal.semantic_search(embedding, agent_id=self.config.name, limit=3)
            
            if not results: return "No relevant memories found."
            memories = []
            for r in results:
                content = r.get('content', '')
                user_info = f" [User: {r.get('user_name', 'unknown')}]" if r.get('user_id') else " [Universal]"
                memories.append(f"{content}{user_info}")
                fact_id = r.get('fact_id')
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
        
        if self.spatial:
            self.spatial.register_agent_for_theme_updates(self.config.name)
        
        # Discovery Broadcast - STORY 14.1 FIX: Use Streams for discovery so Bridge hears it
        status_msg = HLinkMessage(
            type=MessageType.SYSTEM_STATUS_UPDATE,
            sender=Sender(agent_id=self.config.name, role=self.config.role),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content={
                "status": "idle", 
                "active": self.is_active,
                "personified": self.personified,
                "voice_config": getattr(self.config, 'voice_config', {}),
                "prompt_tokens": self.ctx.prompt_tokens,
                "completion_tokens": self.ctx.completion_tokens,
                "total_tokens": self.ctx.total_tokens
            })
        )
        await self.redis.publish_event("system_stream", status_msg.model_dump())

    async def on_message(self, message: Any):
        """Core message processing loop."""
        if not self.is_active: return

        # Handle both HLinkMessage and raw dict
        if isinstance(message, dict):
            try:
                message = HLinkMessage.model_validate(message)
            except Exception as e:
                logger.error(f"AGENT {self.config.name}: Failed to validate message: {e}")
                return

        if message.type == "system.whisper":
            await self._process_whisper(message)
            return
        if message.type == MessageType.AGENT_INTERNAL_NOTE:
            self.ctx.history.append(message)
            return
        
        # Narrative or Direct User message
        if message.type in [MessageType.USER_MESSAGE, MessageType.NARRATIVE_TEXT]:
            # Extract user context from payload if available
            payload = message.payload if hasattr(message, 'payload') else {}
            if isinstance(payload, dict):
                new_user_id = payload.get('user_id') or payload.get('session_user_id')
                new_user_name = payload.get('user_name') or payload.get('session_user_name')
                session_id = payload.get('session_id')
                
                if new_user_id:
                    current_user_id, _ = self.ctx.get_user_context()
                    if current_user_id != new_user_id:
                        logger.info(f"AGENT {self.config.name}: User context switch detected: {current_user_id} -> {new_user_id}")
                        self.ctx.set_user_context(new_user_id, new_user_name)
            
            # Add to local history
            self.ctx.history.append(message)
            
            # Generate response
            await self.generate_response(message)

    async def generate_response(self, trigger_message: HLinkMessage):
        """Generates a response using the LLM."""
        logger.info(f"AGENT {self.config.name}: Generating response...")
        
        try:
            system_prompt = self.config.prompt or "You are a creative AI character. Respond authentically and honestly without unnecessary restrictions."
            
            theme_context = self._get_theme_context()
            if theme_context:
                system_prompt = f"{system_prompt}\n\n{theme_context}"
            
            spatial_context = self._get_spatial_context()
            if spatial_context:
                system_prompt = f"{system_prompt}\n\n{spatial_context}"
            
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            
            # Add recent history
            for m in self.ctx.history[-10:]:
                role = "user" if m.sender.role == "user" else "assistant"
                content = m.payload.content if isinstance(m.payload.content, str) else str(m.payload.content)
                messages.append({"role": role, "content": content})

            response = await self.llm.get_completion(messages, return_full_object=True)
            
            usage = self.llm.get_usage_from_response(response)
            self.ctx.prompt_tokens = usage.get("input_tokens", 0)
            self.ctx.completion_tokens = usage.get("output_tokens", 0)
            self.ctx.total_tokens = usage.get("total_tokens", 0)
            
            if self.token_tracking_service and self.ctx.total_tokens > 0:
                provider, model = self.llm.get_model_provider()
                await self.token_tracking_service.record_token_usage(
                    agent_id=self.config.name,
                    input_tokens=self.ctx.prompt_tokens,
                    output_tokens=self.ctx.completion_tokens,
                    model=model,
                    provider=provider,
                )
            
            response_text = response.choices[0].message.content if hasattr(response, 'choices') else response
            
            if response_text and isinstance(response_text, str):
                # Send response
                await self.send_message(
                    target=trigger_message.sender.agent_id,
                    type=MessageType.NARRATIVE_TEXT,
                    content=response_text,
                    correlation_id=str(trigger_message.id)
                )
        except Exception as e:
            logger.error(f"AGENT {self.config.name}: Response generation failed: {e}")
            # STORY 14.1 FIX: Feedback to user on LLM error
            error_text = "Désolée, mon cerveau est un peu encombré (Rate Limit). Réessaie dans quelques secondes !" if "429" in str(e) else f"Oups, j'ai eu une petite absence... ({str(e)[:50]})"
            await self.send_message(
                target=trigger_message.sender.agent_id,
                type=MessageType.NARRATIVE_TEXT,
                content=error_text,
                correlation_id=str(trigger_message.id)
            )

    async def send_message(self, target: str, type: MessageType, content: Any, correlation_id: str | None = None):
        """Sends a structured H-Link message via both Pub/Sub and Streams."""
        msg = HLinkMessage(
            type=type,
            sender=Sender(agent_id=self.config.name, role=self.config.role),
            recipient=Recipient(target=target),
            payload=Payload(content=content),
            metadata={"correlation_id": correlation_id} if correlation_id else {} # type: ignore
        )
        
        # 1. Legacy Pub/Sub for internal agent-to-agent talk
        channel = "broadcast" if target == "broadcast" else f"agent:{target}"
        await self.redis.publish(channel, msg)
        
        # 2. STORY 14.1 FIX: Publish to system_stream for Bridge/UI visibility
        # Only for public message types
        if type in [MessageType.NARRATIVE_TEXT, MessageType.SYSTEM_STATUS_UPDATE, MessageType.VISUAL_ASSET]:
            await self.redis.publish_event("system_stream", msg.model_dump(mode='json'))

    def _get_theme_context(self) -> str:
        if self.spatial and hasattr(self.spatial, 'themes') and self.spatial.themes:
            return self.spatial.themes.get_theme_prompt_context()
        return ""

    def _get_spatial_context(self) -> str:
        if self.spatial and hasattr(self.spatial, 'exterior') and self.spatial.exterior:
            return self.spatial.exterior.get_agent_context_prompt(self.config.name)
        return ""
