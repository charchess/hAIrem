import asyncio
import inspect
import json
import logging
import os
import random
import re
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
from src.features.admin.token_tracking.pricing import calculate_cost

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

    def __init__(
        self,
        config: AgentConfig,
        redis_client: RedisClient,
        llm_client: LlmClient,
        surreal_client: Any | None = None,
        visual_service: Any | None = None,
        spatial_registry: Any | None = None,
        social_referee: Any | None = None,
        agent_registry: Any | None = None,
        token_tracking_service: Any | None = None,
    ):
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
        self.personified = getattr(self.config, "personified", True)
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
        # Story 15.1: Dynamic Skill Mapping
        # We no longer call _setup_default_tools() here.
        # All tools must be explicitly listed in persona.yaml:skills[]
        self._load_dynamic_skills()

    async def refresh_config(self):
        """
        Refreshes agent configuration following the priority chain:
        1. SurrealDB agent-specific override (config:agent_[name])
        2. SurrealDB global system config (config:system)
        3. Agent manifest (self.config.llm_config)
        4. Environment variables (os.environ)
        """
        logger.info(f"AGENT {self.config.name}: Refreshing configuration...")

        final_config = {}

        # 1. Check SurrealDB for overrides
        if self.surreal:
            agent_override = await self.surreal.get_config(f"agent_{self.config.name}")
            system_config = await self.surreal.get_config("system")

            logger.info(f"DEBUG_CONFIG: Agent override for {self.config.name}: {agent_override}")
            logger.info(f"DEBUG_CONFIG: System config: {system_config}")

            # Extract system-level llm_config if it's nested
            system_llm = system_config.get("llm_config") if system_config else None

            # Combine following priorities
            # Priority 1: Agent override
            if agent_override:
                final_config.update({k: v for k, v in agent_override.items() if v})

            # Priority 2: System config (only for keys not already set)
            if system_llm:
                for k, v in system_llm.items():
                    if k not in final_config or not final_config[k]:
                        final_config[k] = v

        # Priority 3: Manifest
        manifest_llm = self.config.llm_config or {}
        for k, v in manifest_llm.items():
            if k not in final_config or not final_config[k]:
                final_config[k] = v

        # Priority 4: Environment (handled by LlmClient internally if config is empty)
        # But we force the model if we found one

        # Re-initialize LLM Client
        from src.infrastructure.llm import LlmClient

        # Story 7.5: Secure Vault integration
        # Resolve API Key from vault if possible
        provider = final_config.get("provider") or os.getenv("OPENROUTER_API_KEY") and "openrouter" or "openai"
        if self.surreal:
            from src.services.vault.credentials import CredentialVaultService

            vault = CredentialVaultService(self.surreal)

            # 1. Try agent-specific provider key
            vault_key = await vault.get_llm_key(f"{self.config.name}_{provider}")
            # 2. Try global provider key
            if not vault_key:
                vault_key = await vault.get_llm_key(provider)

            if vault_key:
                final_config["api_key"] = vault_key
                logger.info(f"AGENT {self.config.name}: API Key resolved from vault.")

        self.llm = LlmClient(cache=self.llm.cache, config_override=final_config)
        logger.info(f"AGENT {self.config.name}: Config refreshed. Active model: {self.llm.model}")

    def _load_dynamic_skills(self):
        """
        EPIC 15: Dynamic Skill Mapping.
        Loads skills defined in the configuration (persona.yaml).
        Authority: Only skills listed in persona.yaml:skills[] are enabled.
        """
        if not hasattr(self.config, "skills") or not self.config.skills:
            logger.warning(f"AGENT {self.config.name}: No skills defined in persona.yaml.")
            return

        for skill in self.config.skills:
            name = skill.get("name")
            description = skill.get("description")

            if not name or not description:
                continue

            # Case 1: The skill maps to an existing method (Native or Plugin logic.py)
            if hasattr(self, name):
                method = getattr(self, name)
                # Ensure it's callable
                if callable(method):
                    self.tools[name] = {"description": description, "function": method}
                    logger.info(f"AGENT {self.config.name}: Registered skill '{name}' (Method found)")
                    continue

            # Case 2: Placeholder / Future External Plugins
            # We register it so the LLM knows about it, but log it as placeholder
            async def placeholder_handler(**kwargs):
                logger.warning(f"AGENT {self.config.name}: Called unimplemented skill '{name}' with {kwargs}")
                return f"Skill '{name}' is not fully implemented in this agent's logic."

            placeholder_handler.__name__ = name
            self.tools[name] = {"description": description, "function": placeholder_handler}
            logger.info(f"AGENT {self.config.name}: Registered skill '{name}' (Placeholder)")

    async def recall_memory(self, query: str) -> str:
        """Semantic search tool."""
        if not self.surreal:
            return "Memory system is currently unavailable."
        try:
            burning_context = await self._get_burning_memory_context()

            embedding = await self.llm.get_embedding(query)
            if not embedding:
                return "Failed to process search query."

            user_id, user_name = self.ctx.get_user_context()

            if user_id:
                results = await self.surreal.semantic_search_user(embedding, user_id, limit=3)
            else:
                results = await self.surreal.semantic_search(embedding, agent_id=self.config.name, limit=3)

            memories_text = "No relevant past memories found."
            if results:
                memories = []
                for r in results:
                    content = r.get("content", "")
                    user_info = f" [User: {r.get('user_name', 'unknown')}]" if r.get("user_id") else " [Universal]"
                    memories.append(f"{content}{user_info}")
                    fact_id = r.get("fact_id")
                    if fact_id:
                        asyncio.create_task(self.surreal.update_memory_strength(self.config.name, fact_id, boost=True))
                memories_text = "Relevant memories:\n" + "\n".join(memories)

            response = memories_text
            if burning_context:
                response += "\n\n" + burning_context
            return response
        except Exception as e:
            return f"Error during memory recall: {e}"

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Returns the schema of registered tools for LLM."""
        schemas = []
        for name, details in self.tools.items():
            func = details["function"]
            description = details["description"]
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            )
        return schemas

    async def send_internal_note(self, target_agent: str, content: str) -> str:
        """Sends a private H-Link message to another agent."""
        note_msg = HLinkMessage(
            type=MessageType.AGENT_INTERNAL_NOTE,
            sender=Sender(agent_id=self.config.name, role=self.config.role),
            recipient=Recipient(target=target_agent),
            payload=Payload(content=content),
        )
        channel = "broadcast" if target_agent == "broadcast" else f"agent:{target_agent}"
        await self.redis.publish(channel, note_msg)
        return f"Note successfully sent to {target_agent}."

    async def generate_image(self, prompt: str, style: str = "cinematic") -> str:
        """Generate an image using the visual service."""
        if not self.visual_service:
            return "Visual service is not available."
        try:
            asset_uri, _ = await self.visual_service.generate_and_index(
                agent_id=self.config.name, prompt=prompt, style_preset=style
            )
            return f"Image successfully generated: {asset_uri}"
        except Exception as e:
            return f"Failed to generate image: {e}"

    def tool(self, description: str):
        """Decorator to register a method as an LLM-accessible tool."""

        def decorator(func):
            tool_name = func.__name__
            self.tools[tool_name] = {"description": description, "function": func}
            return func

        return decorator

    async def start(self):
        """Starts the agent loop."""
        # Initial config resolution
        await self.refresh_config()

        channel = f"agent:{self.config.name}"
        broadcast_channel = "agent:broadcast"

        # FIX: Robustly handle mock/real redis subscribe
        # Real redis returns coroutine, Mock usually returns AsyncMock
        try:
            res = self.redis.subscribe(channel, self.on_message)
            if inspect.isawaitable(res):
                self._own_task = asyncio.create_task(res)

            res_bc = self.redis.subscribe(broadcast_channel, self.on_message)
            if inspect.isawaitable(res_bc):
                self._broadcast_task = asyncio.create_task(res_bc)
        except Exception as e:
            logger.warning(f"Failed to subscribe tasks (likely mock): {e}")

        if self.spatial:
            self.spatial.register_agent_for_theme_updates(self.config.name)

        # Calculate cost
        provider = self.config.llm_config.get("provider", "openai") if self.config.llm_config else "openai"
        model = self.config.llm_config.get("model", "gpt-4") if self.config.llm_config else "gpt-4"
        cost = calculate_cost(provider, model, self.ctx.prompt_tokens, self.ctx.completion_tokens)

        # Discovery Broadcast - STORY 14.1 FIX: Use Streams for discovery so Bridge hears it
        status_msg = HLinkMessage(
            type=MessageType.SYSTEM_STATUS_UPDATE,
            sender=Sender(agent_id=self.config.name, role=self.config.role),
            recipient=Recipient(target="broadcast"),
            payload=Payload(
                content={
                    "status": "idle",
                    "active": self.is_active,
                    "personified": self.personified,
                    "voice_config": getattr(self.config, "voice_config", {}),
                    "prompt_tokens": self.ctx.prompt_tokens,
                    "completion_tokens": self.ctx.completion_tokens,
                    "total_tokens": self.ctx.total_tokens,
                    "cost": cost,
                }
            ),
        )

        # Robust stream publish
        try:
            res = self.redis.publish_event("system_stream", status_msg.model_dump())
            if inspect.isawaitable(res):
                await res
        except Exception as e:
            logger.warning(f"Failed to publish system status (mock?): {e}")

    async def stop(self):
        """Stops the agent and cancels background tasks."""
        logger.info(f"AGENT {self.config.name}: Stopping...")
        if self._own_task:
            self._own_task.cancel()
        if self._broadcast_task:
            self._broadcast_task.cancel()

        # Cleanup
        try:
            await asyncio.gather(self._own_task, self._broadcast_task, return_exceptions=True)
        except Exception:
            pass

        logger.info(f"AGENT {self.config.name}: Stopped.")

    async def on_message(self, message: Any):
        """Core message processing loop."""
        if not self.is_active:
            return

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
        if message.type == MessageType.EXPERT_COMMAND:
            await self._handle_command(message)
            return

        if message.type == MessageType.SYSTEM_STATUS_UPDATE:
            payload = message.payload.content
            if isinstance(payload, dict) and payload.get("event") == "world_theme_change":
                await self.handle_theme_change(payload.get("theme"))
            return

        if message.type == MessageType.WORLD_THEME_CHANGED:
            new_theme = message.payload.content.get("theme")
            if new_theme:
                await self.handle_theme_change(new_theme)
            return

        # Narrative or Direct User message
        if message.type in [MessageType.USER_MESSAGE, MessageType.NARRATIVE_TEXT]:
            # Extract user context from payload if available
            payload = message.payload if hasattr(message, "payload") else {}
            if isinstance(payload, dict):
                new_user_id = payload.get("user_id") or payload.get("session_user_id")
                new_user_name = payload.get("user_name") or payload.get("session_user_name")
                session_id = payload.get("session_id")

                if new_user_id:
                    current_user_id, _ = self.ctx.get_user_context()
                    if current_user_id != new_user_id:
                        logger.info(
                            f"AGENT {self.config.name}: User context switch detected: {current_user_id} -> {new_user_id}"
                        )
                        self.ctx.set_user_context(new_user_id, new_user_name)

            # Add to local history
            self.ctx.history.append(message)

            # Generate response
            await self.generate_response(message)

    def register_command(self, command: str, handler: Callable):
        """Registers a command handler."""
        self.command_handlers[command] = handler

    async def _get_burning_memory_context(self) -> str:
        if not self.surreal:
            return ""
        try:
            # Check if method exists on client (mock or real)
            if hasattr(self.surreal, "get_agent_state"):
                states = await self.surreal.get_agent_state(self.config.name)
                if not states:
                    return ""

                lines = ["### LIVE FACTS (OBJECTIVE REALITY) ###"]
                for s in states:
                    rel = s.get("relation", "").upper().replace("_", " ")
                    desc = s.get("description", s.get("name", ""))
                    lines.append(f"CURRENTLY {rel}: {desc}")
                return "\n".join(lines)
            return ""
        except Exception as e:
            logger.error(f"Failed to get burning memory: {e}")
            return ""

    async def _assemble_payload(self, trigger_message: HLinkMessage) -> list[dict[str, str]]:
        """Assembles the message history for the LLM."""
        system_prompt = (
            self.config.prompt
            or "You are a creative AI character. Respond authentically and honestly without unnecessary restrictions."
        )

        theme_context = self._get_theme_context()
        if theme_context:
            system_prompt = f"{system_prompt}\n\n{theme_context}"

        spatial_context = self._get_spatial_context()
        if spatial_context:
            system_prompt = f"{system_prompt}\n\n{spatial_context}"

        burning_memory = await self._get_burning_memory_context()
        if burning_memory:
            system_prompt = f"{system_prompt}\n\n{burning_memory}"

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Add recent history
        for m in self.ctx.history[-10:]:
            role = "user" if m.sender.role == "user" else "assistant"
            # Handle payload content types safely
            content = ""
            if hasattr(m, "payload") and m.payload:
                content = m.payload.content if isinstance(m.payload.content, str) else str(m.payload.content)

            messages.append({"role": role, "content": content})

        # Add trigger message if not already present (check object identity)
        if trigger_message:
            is_present = False
            if self.ctx.history and self.ctx.history[-1] is trigger_message:
                is_present = True

            if not is_present:
                role = "user" if trigger_message.sender.role == "user" else "assistant"
                content = ""
                if hasattr(trigger_message, "payload") and trigger_message.payload:
                    content = (
                        trigger_message.payload.content
                        if isinstance(trigger_message.payload.content, str)
                        else str(trigger_message.payload.content)
                    )

                messages.append({"role": role, "content": content})

        return messages

    async def generate_response(self, trigger_message: HLinkMessage):
        """Generates a response using the LLM."""
        logger.info(f"AGENT {self.config.name}: Generating response...")

        try:
            messages = await self._assemble_payload(trigger_message)

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

            response_text = response.choices[0].message.content if hasattr(response, "choices") else response

            if response_text and isinstance(response_text, str):
                # Update stats in social arbiter if present
                if self.social and hasattr(self.social, "update_agent_stats"):
                    # We don't have precise timing here, let's assume 1.0s or use actual diff
                    self.social.update_agent_stats(self.config.name, 1.0)

                # Send response
                await self.send_message(
                    target=trigger_message.sender.agent_id,
                    type=MessageType.NARRATIVE_TEXT,
                    content=response_text,
                    correlation_id=str(trigger_message.id),
                )
        except Exception as e:
            logger.error(f"AGENT {self.config.name}: Response generation failed: {e}")
            # STORY 14.1 FIX: Feedback to user on LLM error
            error_text = (
                "Désolée, mon cerveau est un peu encombré (Rate Limit). Réessaie dans quelques secondes !"
                if "429" in str(e)
                else f"Oups, j'ai eu une petite absence... ({str(e)[:50]})"
            )
            await self.send_message(
                target=trigger_message.sender.agent_id,
                type=MessageType.NARRATIVE_TEXT,
                content=error_text,
                correlation_id=str(trigger_message.id),
            )

    async def send_message(self, target: str, type: MessageType, content: Any, correlation_id: str | None = None):
        """Sends a structured H-Link message via both Pub/Sub and Streams."""
        msg = HLinkMessage(
            type=type,
            sender=Sender(agent_id=self.config.name, role=self.config.role),
            recipient=Recipient(target=target),
            payload=Payload(content=content),
            metadata={"correlation_id": correlation_id} if correlation_id else {},  # type: ignore
        )

        # 1. Legacy Pub/Sub for internal agent-to-agent talk
        channel = "broadcast" if target == "broadcast" else f"agent:{target}"
        await self.redis.publish(channel, msg)

        # 2. STORY 14.1 FIX: Publish to system_stream for Bridge/UI visibility
        # Only for public message types
        if type in [MessageType.NARRATIVE_TEXT, MessageType.SYSTEM_STATUS_UPDATE, MessageType.VISUAL_ASSET]:
            await self.redis.publish_event("system_stream", msg.model_dump(mode="json"))

    def _get_theme_context(self) -> str:
        if self.spatial and hasattr(self.spatial, "themes") and self.spatial.themes:
            return self.spatial.themes.get_theme_prompt_context()
        return ""

    @property
    def system_prompt(self) -> str:
        """Returns the system prompt for the agent."""
        return (
            self.config.prompt
            or "You are a creative AI character. Respond authentically and honestly without unnecessary restrictions."
        )

    async def _handle_command(self, message: HLinkMessage):
        """Executes a registered command."""
        payload_content = message.payload.content
        command_name = ""

        if isinstance(payload_content, dict):
            command_name = payload_content.get("command")

        if command_name and command_name in self.command_handlers:
            try:
                handler = self.command_handlers[command_name]
                # Pass payload content to handler
                if inspect.iscoroutinefunction(handler):
                    result = await handler(payload_content)
                else:
                    result = handler(payload_content)

                # Send success response
                await self.send_message(
                    target=message.sender.agent_id,
                    type=MessageType.EXPERT_RESPONSE,
                    content={"result": result, "status": "success"},
                    correlation_id=str(message.id),
                )
            except Exception as e:
                logger.error(f"Command {command_name} failed: {e}")
                await self.send_message(
                    target=message.sender.agent_id,
                    type=MessageType.EXPERT_RESPONSE,
                    content={"result": None, "status": "error", "error": str(e)},
                    correlation_id=str(message.id),
                )
        else:
            logger.warning(f"Unknown command: {command_name}")

    def _get_theme_context(self) -> str:
        if self.spatial and hasattr(self.spatial, "themes") and self.spatial.themes:
            return self.spatial.themes.get_theme_prompt_context()
        return ""

    def _check_addressing(self, content: str) -> bool:
        """Checks if the message is addressed to specific agent."""
        name = self.config.name.lower()
        content_lower = content.lower()

        # Robust regex check for name as a whole word
        # Matches @Name, Name, Name?, "to Name", "Salut Name"
        if re.search(r"(@|\b)" + re.escape(name) + r"\b", content_lower):
            return True

        return False

    async def handle_theme_change(self, new_theme: str):
        """Reacts to a global theme change (Epic 18)."""
        logger.info(f"AGENT {self.config.name}: World theme changed to '{new_theme}'. Cascading visuals...")

        if not new_theme:
            return

        # Data-driven cascade: check if agent has a specific response for this theme
        theme_cfg = self.config.theme_responses.get(new_theme)

        if not theme_cfg:
            # Try case-insensitive fallback
            for k, v in self.config.theme_responses.items():
                if k.lower() == new_theme.lower():
                    theme_cfg = v
                    break

        if theme_cfg:
            # 1. Change Outfit if specified
            if "outfit" in theme_cfg:
                await self.change_outfit(theme_cfg["outfit"])

            # 2. Add an internal note to reflect on the change
            note_msg = HLinkMessage(
                type=MessageType.AGENT_INTERNAL_NOTE,
                sender=Sender(agent_id="system", role="orchestrator"),
                recipient=Recipient(target=self.config.name),
                payload=Payload(
                    content=f"The world has changed to {new_theme}. My reaction: {theme_cfg.get('internal_thought', 'Acceptance')}"
                ),
            )
            self.ctx.history.append(note_msg)

            logger.info(f"AGENT {self.config.name}: Applied custom response for theme '{new_theme}'")
        else:
            logger.debug(f"AGENT {self.config.name}: No specific response defined for theme '{new_theme}'")

    async def move_to(self, location_name: str) -> str:
        """Moves the agent to a new location via Spatial service."""
        # Detect if actually changing room
        # (In a real implementation we'd check DB first, but for now we always 'move')

        note_msg = HLinkMessage(
            type=MessageType.AGENT_INTERNAL_NOTE,
            sender=Sender(agent_id="system", role="orchestrator"),
            recipient=Recipient(target=self.config.name),
            payload=Payload(content=f"I have moved to the {location_name} to be with the user."),
        )
        self.ctx.history.append(note_msg)

        if self.spatial and hasattr(self.spatial, "move_agent"):
            await self.spatial.move_agent(self.config.name, location_name)
            return f"Success: Moved to {location_name}"

        # Fallback to direct DB update if service missing
        if self.surreal:
            await self.surreal.update_agent_state(
                self.config.name, "IS_IN", {"name": location_name, "description": f"The {location_name}"}
            )
            return f"Success: Moved to {location_name} (Direct)"

        return "Spatial service unavailable."

    async def change_outfit(self, description: str) -> str:
        """Changes the agent's outfit."""
        if self.visual_service:
            try:
                await self.visual_service.generate_and_index(
                    agent_id=self.config.name, prompt=description, style_preset="cinematic"
                )
            except Exception as e:
                logger.error(f"Visual generation failed: {e}")

        if self.surreal:
            await self.surreal.update_agent_state(
                self.config.name, "WEARS", {"name": "outfit", "description": description}
            )
        return "Success: Outfit changed."

    def _get_spatial_context(self) -> str:
        if self.spatial and hasattr(self.spatial, "exterior") and self.spatial.exterior:
            return self.spatial.exterior.get_agent_context_prompt(self.config.name)
        return ""
