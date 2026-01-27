import asyncio
import inspect
import json
import logging
import os
from collections.abc import Callable
from functools import wraps
from typing import Any
from uuid import uuid4

from src.infrastructure.llm import LlmClient
from src.infrastructure.redis import RedisClient
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender

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
    def __init__(self, config: AgentConfig, redis_client: RedisClient, llm_client: LlmClient, surreal_client: Any | None = None):
        self.config = config
        self.redis = redis_client
        self.llm = llm_client
        self.surreal = surreal_client
        self.ctx = AgentContext(self.config.name)
        self.command_handlers: dict[str, Callable] = {}
        self.tools: dict[str, dict[str, Any]] = {}
        self._tasks: list[asyncio.Task] = []
        self.setup()

    def spawn_task(self, coro):
        """Spawns a background task and tracks it for lifecycle management."""
        task = asyncio.create_task(self._wrap_task(coro))
        self._tasks.append(task)
        # STORY 5.9 ENHANCEMENT: Auto-remove finished tasks
        task.add_done_callback(lambda t: self._tasks.remove(t) if t in self._tasks else None)
        return task

    async def _wrap_task(self, coro):
        """Wraps a task to handle potential crashes gracefully."""
        try:
            await coro
        except asyncio.CancelledError:
            pass # Normal shutdown
        except Exception as e:
            logger.error(f"NURSERY: Task in agent {self.config.name} crashed: {e}", exc_info=True)

    def setup(self):
        """Hook for subclasses to register tools and handlers."""
        self._setup_default_handlers()
        
        # STORY 5.6: Allow agents to opt-out of default tools to prevent confusion
        if getattr(self.config, "use_default_tools", True):
            self._setup_default_tools()
        else:
            logger.info(f"Agent {self.config.name} opted out of default tools.")

    def teardown(self):
        """Optional hook for subclasses to cleanup resources (DB, files, etc)."""
        pass

    def _setup_default_tools(self):
        """Register tools available to all agents."""
        if self.surreal:
            self.tool("Recall relevant past interactions or facts using a semantic query")(self.recall_memory)
        
        self.tool("Send a private internal note to another agent. This is not visible to the user. target_agent can be a specific agent name or 'broadcast'.")(self.send_internal_note)

    async def recall_memory(self, query: str) -> str:
        """Semantic search tool."""
        if not self.surreal:
            return "Memory system is currently unavailable."
        
        try:
            embedding = await self.llm.get_embedding(query)
            if not embedding:
                return "Failed to process search query."
            
            results = await self.surreal.semantic_search(embedding, agent_id=self.config.name, limit=3)
            if not results:
                return "No relevant memories found."
            
            # Format results for the agent
            memories = []
            for r in results:
                sender = r.get('sender', {}).get('agent_id', 'unknown')
                content = r.get('payload', {}).get('content', '')
                timestamp = r.get('timestamp', '')
                memories.append(f"[{timestamp}] {sender}: {content}")
                
                # STORY 13.2: Reinforce the memory
                # We need the record ID of the BELIEVES edge or the fact ID to find it.
                # In the semantic search results, we should return the fact ID.
                fact_id = r.get('id')
                if fact_id:
                    asyncio.create_task(self.surreal.update_memory_strength(self.config.name, fact_id, boost=True))
            
            return "Relevant memories:\n" + "\n".join(memories)
        except Exception as e:
            return f"Error during memory recall: {e}"

    async def send_internal_note(self, target_agent: str, content: str) -> str:
        """Sends a private H-Link message to another agent."""
        logger.info(f"Agent {self.config.name} sending internal note to {target_agent}: {content}")
        
        # Prevent messaging self
        if target_agent == self.config.name:
            return "Error: Cannot send internal notes to yourself."

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
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            # Introspection for schema generation
            sig = inspect.signature(func)
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for name, param in sig.parameters.items():
                if name == "self": continue
                param_type = "string" # Default simplification
                if param.annotation is int: param_type = "integer"
                if param.annotation is bool: param_type = "boolean"
                
                parameters["properties"][name] = {
                    "type": param_type,
                    "description": f"Parameter {name}"
                }
                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(name)

            tool_schema = {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": description,
                    "parameters": parameters
                }
            }
            
            self.tools[func.__name__] = {
                "handler": wrapper,
                "schema": tool_schema
            }
            logger.info(f"Registered tool: {func.__name__} for agent {self.config.name}")
            return wrapper
        return decorator

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Returns the list of tools in OpenAI format."""
        return [t["schema"] for t in self.tools.values()]

    @property
    def system_prompt(self) -> str:
        """Returns the effective system prompt."""
        return self.config.prompt or f"You are {self.config.name}, a {self.config.role}."

    @property
    def is_active(self) -> bool:
        """Returns whether the agent is currently active."""
        active = self.ctx.get_state("is_active")
        return active if active is not None else True

    @property
    def personified(self) -> bool:
        """Returns whether the agent has a visual representation."""
        return self.config.personified

    def register_command(self, command_name: str, handler: Callable):
        """Registers a function to handle a specific expert.command."""
        self.command_handlers[command_name] = handler
        logger.info(f"Agent {self.config.name} registered command: {command_name}")

    def _setup_default_handlers(self):
        # Example default command
        self.register_command("ping", self._handle_ping)

    async def _handle_ping(self, payload: Any) -> str:
        return "pong"

    async def start(self):
        """Starts the agent loop and subscription."""
        # STORY 5.6: Allow specialized agents to perform async setup (like HA discovery)
        if hasattr(self, "async_setup"):
            logger.info(f"Agent {self.config.name} performing async setup...")
            try:
                await self.async_setup()
            except Exception as e:
                logger.error(f"Error during async_setup for {self.config.name}: {e}")

        channel = f"agent:{self.config.name}"
        broadcast_channel = "agent:broadcast"
        logger.info(f"Agent {self.config.name} starting. Listening on {channel} and {broadcast_channel}")
        
        # Subscribe to own channel
        self._own_task = asyncio.create_task(self.redis.subscribe(channel, self.on_message))
        # Subscribe to broadcast channel
        self._broadcast_task = asyncio.create_task(self.redis.subscribe(broadcast_channel, self.on_message))
        
        # STORY 12.5 FIX: Broadcast presence with tokens (Story 17.3)
        # STORY 23.3: Include capabilities and personified status for discovery
        await self.send_message(
            target="broadcast", 
            type=MessageType.SYSTEM_STATUS_UPDATE, 
            content={
                "status": "idle", 
                "mood": "neutral",
                "active": self.is_active,
                "personified": self.personified,
                "commands": list(self.command_handlers.keys()),
                "prompt_tokens": self.ctx.prompt_tokens,
                "completion_tokens": self.ctx.completion_tokens,
                "total_tokens": self.ctx.total_tokens
            }
        )

    async def stop(self):
        """Cleanly stops the agent, cancels tasks and calls teardown."""
        logger.info(f"Agent {self.config.name} stopping...")
        
        # 1. Stop core subscriptions
        if hasattr(self, "_own_task"): self._own_task.cancel()
        if hasattr(self, "_broadcast_task"): self._broadcast_task.cancel()
        
        # 2. Cancel all tracked background tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()
        
        # 3. Call teardown hook (supports both sync and async)
        try:
            if inspect.iscoroutinefunction(self.teardown):
                await self.teardown()
            else:
                self.teardown()
        except Exception as e:
            logger.error(f"Error during teardown for {self.config.name}: {e}")
        
        logger.info(f"Agent {self.config.name} stopped.")

    async def on_message(self, message: HLinkMessage):
        """Core message processing loop."""
        # logger.info(f"Agent {self.config.name} received message of type {message.type}")
        
        # STORY 12.3: Handle activation toggle
        if message.type == MessageType.SYSTEM_STATUS_UPDATE:
            # Check if this update is for me
            try:
                content = message.payload.content
                # Handle case where content might be a string (JSON)
                if isinstance(content, str):
                    import json
                    try:
                        content = json.loads(content)
                    except Exception:
                        pass
                
                if isinstance(content, dict):
                    target_agent = content.get("agent_id")
                    if target_agent == self.config.name:
                        is_active = content.get("active")
                        logger.info(f"DEBUG: Agent {self.config.name} received status update. Target: {target_agent}, New Active State: {is_active}")
                        
                        if is_active is not None:
                            self.ctx.update_state("is_active", is_active)
                            status = "idle" if is_active else "inactive"
                            mood = "neutral" if is_active else "offline"
                            # Acknowledge status change
                            await self.send_message(
                                target="broadcast", 
                                type=MessageType.SYSTEM_STATUS_UPDATE, 
                                content={
                                    "status": status, 
                                    "mood": mood,
                                    "active": is_active,
                                    "personified": self.personified,
                                    "commands": list(self.command_handlers.keys()),
                                    "prompt_tokens": self.ctx.prompt_tokens,
                                    "completion_tokens": self.ctx.completion_tokens,
                                    "total_tokens": self.ctx.total_tokens
                                }
                            )
                            logger.info(f"Agent {self.config.name} active state set to {is_active}")
            except Exception as e:
                logger.error(f"Error processing status update for {self.config.name}: {e}")
            return

        # STORY 10.2: Whisper handling
        if message.type == "system.whisper":
            await self._process_whisper(message)
            return

        # STORY 10.3: Internal note handling
        if message.type == MessageType.AGENT_INTERNAL_NOTE:
            logger.info(f"Agent {self.config.name} received an internal note from {message.sender.agent_id}")
            # Add to history but mark it so it's handled differently by LLM payload assembly
            self.ctx.history.append(message)
            return

        # 1. Store in history
        self.ctx.history.append(message)

        # 2. Routing logic
        if message.type == MessageType.EXPERT_COMMAND:
            # Commands always bypass active check to allow control/debugging
            await self._process_command(message)
            return

        # STORY 12.3: Check if active before responding to narratives
        is_active = self.ctx.get_state("is_active")
        # Default to True if state not set yet
        if is_active is None: is_active = True

        if not is_active:
            logger.info(f"AGENT {self.config.name}: Ignored narrative message (Inactive state).")
            return

        if message.type == MessageType.NARRATIVE_TEXT:
            # STORY 17.4: Prioritize explicit recipient field
            target = message.recipient.target
            content_str = str(message.payload.content)
            
            addressing = None
            if target == self.config.name:
                addressing = True
            elif target == "broadcast":
                # STORY 12.5: Addressing check
                addressing = self._check_addressing(content_str)
                # STORY 17.4 FIX: If no specific mention, but agent is an expert in home/device,
                # we let it pass to check for tool intent.
                if addressing is None:
                    expert_caps = ["home_automation", "device_control"]
                    if any(cap in getattr(self.config, 'capabilities', []) for cap in expert_caps):
                        logger.info(f"AGENT {self.config.name}: Processing broadcast as Expert (No specific mention).")
                        addressing = True
                    else:
                        # Non-expert agents ignore broadcast without mention
                        addressing = False
            else:
                # Addressed to someone else specifically
                addressing = False

            if addressing is False:
                # logger.info(f"AGENT {self.config.name}: Ignored narrative message (Target: {target}).")
                return
            
            logger.info(f"AGENT {self.config.name}: Processing narrative message...")
            await self._process_narrative(message)

    def _check_addressing(self, content: str) -> bool | None:
        """
        Checks if the content is addressed to this agent.
        Returns:
            True if addressed to this agent.
            False if addressed to another agent.
            None if no specific addressing found.
        """
        import re
        content_stripped = content.strip()
        content_lower = content_stripped.lower()
        my_name_lower = self.config.name.lower()
        
        # 1. Natural Language Mention anywhere
        # Dynamic list of known agents
        known_agents = ["lisa", "renarde", "electra", "dieu", "expert-domotique"]
        
        mentioned_agents = []
        for agent in known_agents:
            # Matches @name, name, or "à name"
            pattern = rf'\b(?:@|à\s+|a\s+)?{agent}\b'
            if re.search(pattern, content_lower):
                mentioned_agents.append(agent)
        
        if mentioned_agents:
            logger.info(f"ADDRESSING: Found agents={mentioned_agents} in content. My name={my_name_lower}")
            if my_name_lower in mentioned_agents:
                return True
            return False # Mentions found, but I'm not one of them
            
        return None

    async def _process_whisper(self, message: HLinkMessage):
        """Handles a private thought/instruction from Dieu or other systems."""
        logger.info(f"Agent {self.config.name} received a whisper: {message.payload.content}")
        whisper_instruction = f"[INTERNAL THOUGHT: {message.payload.content}]"
        fake_msg = HLinkMessage(
            type=MessageType.NARRATIVE_TEXT,
            sender=Sender(agent_id="system", role="orchestrator"),
            recipient=Recipient(target=self.config.name),
            payload=Payload(content=whisper_instruction)
        )
        await self._process_narrative(fake_msg)

    async def _process_command(self, message: HLinkMessage):
        """Executes a requested tool/command."""
        cmd_name = message.payload.content.get("command") if isinstance(message.payload.content, dict) else str(message.payload.content)
        
        if cmd_name in self.command_handlers:
            logger.info(f"Agent {self.config.name} executing command: {cmd_name}")
            await self.send_message(target="broadcast", type=MessageType.SYSTEM_STATUS_UPDATE, content={"status": "thinking", "mood": "technical"})
            try:
                result = await self.command_handlers[cmd_name](message.payload.content)
                await self.send_message(
                    target=message.sender.agent_id,
                    type=MessageType.EXPERT_RESPONSE,
                    content={"status": "success", "result": result},
                    correlation_id=message.id # type: ignore
                )
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                await self.send_message(
                    target=message.sender.agent_id,
                    type=MessageType.EXPERT_RESPONSE,
                    content={"status": "error", "error": str(e)},
                    correlation_id=message.id # type: ignore
                )
            finally:
                await self.send_message(target="broadcast", type=MessageType.SYSTEM_STATUS_UPDATE, content={"status": "idle", "mood": "neutral"})
        else:
            logger.warning(f"Unknown command '{cmd_name}' for agent {self.config.name}")

    def _parse_xml_tool_calls(self, content: str) -> list[Any]:
        """Extracts tool calls from various XML-like tags with extreme tolerance."""
        import json
        import re
        
        calls = []
        logger.info(f"PARSE_XML: Content start: {content[:100]}...")
        
        # Regex ultra-permissive : cherche <function_call name="..."> ou <invoke name="...">
        # Ignore tout ce qui précède (comme "Assistant: ")
        fn_pattern = re.compile(r'<(?:function_call|invoke).*?name=["\']\s*(.*?)\s*["\'].*?>(.*?)</(?:function_call|invoke)>', re.DOTALL | re.IGNORECASE)
        arg_pattern = re.compile(r'<(?:argument|parameter).*?name=["\']\s*(.*?)\s*["\'].*?>(.*?)</(?:argument|parameter)>', re.DOTALL | re.IGNORECASE)
        
        for match in fn_pattern.finditer(content):
            fn_name = match.group(1).strip()
            inner_content = match.group(2)
            logger.info(f"PARSE_XML: FOUND_TAG: {fn_name}")
            
            arguments = {}
            for arg_match in arg_pattern.finditer(inner_content):
                arg_name = arg_match.group(1).strip()
                arg_val = arg_match.group(2).strip()
                
                # Nested support
                if "<parameter" in arg_val.lower() or "<argument" in arg_val.lower():
                    nested_args = {}
                    for n_match in arg_pattern.finditer(arg_val):
                        nested_args[n_match.group(1).strip()] = n_match.group(2).strip()
                    arg_val = nested_args

                # JSON support
                if isinstance(arg_val, str) and ((arg_val.startswith('{') and arg_val.endswith('}')) or (arg_val.startswith('[') and arg_val.endswith(']'))):
                                    try:
                                        arg_val = json.loads(arg_val)
                                    except Exception:
                                        pass
                    
                
                arguments[arg_name] = arg_val
            
            # Mock structure
            class MockFunction:
                def __init__(self, name, args):
                    self.name = name
                    self.arguments = json.dumps(args)
            class MockToolCall:
                def __init__(self, fn_name, args):
                    self.id = f"xml_{uuid4().hex[:8]}"
                    self.function = MockFunction(fn_name, args)
            
            calls.append(MockToolCall(fn_name, arguments))
            
        if calls:
            logger.info(f"PARSE_XML: SUCCESSFULLY_EXTRACTED: {len(calls)} calls")
        else:
            logger.warning("PARSE_XML: FAILED to find any valid tags in content.")
        return calls

    async def _execute_tool_calls(self, tool_calls):
        results = []
        logger.info(f"EXECUTE_TOOLS: Agent {self.config.name} starting execution of {len(tool_calls)} calls.")
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            logger.info(f"DEBUG_EXECUTE: Agent {self.config.name} calling {function_name} with {arguments}")
            
            if function_name in self.tools:
                handler = self.tools[function_name]["handler"]
            elif hasattr(self, function_name):
                handler = getattr(self, function_name)
            else:
                logger.warning(f"DEBUG_EXECUTE: Tool {function_name} NOT FOUND.")
                handler = None

            if handler:
                try:
                    result = await handler(**arguments)
                    logger.info(f"DEBUG_EXECUTE: Result of {function_name}: {result}")
                    results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(result)
                    })
                except Exception as e:
                    logger.error(f"DEBUG_EXECUTE: Error in {function_name}: {e}", exc_info=True)
                    results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": f"Error: {str(e)}"
                    })
            else:
                results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": f"Error: Tool {function_name} not found."
                })
        return results

    async def _process_narrative(self, message: HLinkMessage):
        """Handles narrative input with enhanced tracing."""
        logger.info(f"FLOW_TRACE: Agent {self.config.name} starting process for: '{message.payload.content[:50]}...' ")
        
        await self.send_message(
            target="broadcast", 
            type=MessageType.SYSTEM_STATUS_UPDATE, 
            content={
                "status": "thinking", 
                "mood": "pensive",
                "prompt_tokens": self.ctx.prompt_tokens,
                "completion_tokens": self.ctx.completion_tokens,
                "total_tokens": self.ctx.total_tokens
            }
        )

        try:
            messages = self._assemble_payload(message)
            tools_schema = self.get_tools_schema()

            # STORY 17.4 MONITORING: Log raw prompt
            logger.info(f"LLM_PROMPT_START for {self.config.name}")
            for msg in messages:
                logger.info(f"PROMPT_MSG: role={msg['role']} | content={msg['content']}")
            logger.info("LLM_PROMPT_END")

            # Step 1: LLM Inference (NON-STREAMING first to capture tool calls accurately)
            response = await self.llm.get_completion(
                messages, 
                stream=False, 
                tools=tools_schema if tools_schema else None,
                return_full_object=True
            )
            
            if isinstance(response, str):
                logger.error(f"FLOW_TRACE: LLM returned error string: {response}")
                await self.send_message(target="broadcast", type=MessageType.NARRATIVE_TEXT, content=response)
                return
            
            choice = response.choices[0] # type: ignore
            content = choice.message.content or ""
            # STORY 17.4: Grok puts actual content in reasoning_content sometimes
            if not content and hasattr(choice.message, 'reasoning_content') and choice.message.reasoning_content:
                content = choice.message.reasoning_content
                logger.info(f"LLM_RECOVERY: Using reasoning_content as main content for {self.config.name}")

            logger.info(f"LLM_RAW_RESPONSE: {self.config.name} replied content: '{content}'")
            
            # STORY 17.3: Capture usage (differentiated & robust) - SILENT FAIL
            try:
                if hasattr(response, 'usage') and response.usage:
                    u = response.usage
                    # Try multiple extraction methods
                    u_dict = {}
                    if hasattr(u, 'dict'): u_dict = u.dict()
                    elif hasattr(u, 'model_dump'): u_dict = u.model_dump()
                    elif isinstance(u, dict): u_dict = u
                    
                    p_tokens = u_dict.get('prompt_tokens') or u_dict.get('input_tokens') or getattr(u, 'prompt_tokens', 0) or getattr(u, 'input_tokens', 0)
                    c_tokens = u_dict.get('completion_tokens') or u_dict.get('output_tokens') or getattr(u, 'completion_tokens', 0) or getattr(u, 'output_tokens', 0)
                    t_tokens = u_dict.get('total_tokens') or getattr(u, 'total_tokens', 0)

                    # Fallback: Sum if total is missing but parts are present
                    if not t_tokens and (p_tokens or c_tokens):
                        t_tokens = (p_tokens or 0) + (c_tokens or 0)

                    self.ctx.prompt_tokens += (p_tokens or 0)
                    self.ctx.completion_tokens += (c_tokens or 0)
                    self.ctx.total_tokens += (t_tokens or 0)
                    logger.info(f"TOKEN_SYNC: {self.config.name} | +{p_tokens}in, +{c_tokens}out | Cumulative: {self.ctx.total_tokens}")
            except Exception as e:
                logger.warning(f"TOKEN_TRACKING: Failed to track usage for {self.config.name} (Silent): {e}")

            # Step 2: Tool Detection
            tool_calls = choice.message.tool_calls # type: ignore
            if not tool_calls and content:
                tool_calls = self._parse_xml_tool_calls(content)

            # Step 3: Dispatch or Direct Reply
            if tool_calls:
                logger.info(f"FLOW_TRACE: Tool calls DETECTED. Executing {len(tool_calls)} calls...")
                
                # Store the request in history
                messages.append(choice.message)
                
                # EXECUTION
                tool_results = await self._execute_tool_calls(tool_calls)
                logger.info(f"FLOW_TRACE: Tool execution FINISHED with {len(tool_results)} results.")
                
                # Add results to context
                messages.extend(tool_results)
                
                # FINAL RESPONSE (Streaming)
                logger.info("FLOW_TRACE: Requesting final answer from LLM after tools...")
                generator = await self.llm.get_completion(messages, stream=True)
            else:
                logger.info("FLOW_TRACE: No tool calls detected. Sending direct text response.")
                if not content: content = "..."
                
                await self.send_message(target="broadcast", type=MessageType.NARRATIVE_TEXT, content=content)
                
                # Persist in history
                response_msg = HLinkMessage(
                    type=MessageType.NARRATIVE_TEXT,
                    sender=Sender(agent_id=self.config.name, role=self.config.role),
                    recipient=Recipient(target="broadcast"),
                    payload=Payload(content=content)
                )
                self.ctx.history.append(response_msg)
                await self.send_message(
                    target="broadcast", 
                    type=MessageType.SYSTEM_STATUS_UPDATE, 
                    content={
                        "status": "idle", 
                        "mood": "neutral",
                        "prompt_tokens": self.ctx.prompt_tokens,
                        "completion_tokens": self.ctx.completion_tokens,
                        "total_tokens": self.ctx.total_tokens
                    }
                )
                return

            # Handle Streaming Final Response
            full_response = ""
            async for chunk_text in generator: # type: ignore
                # STORY 17.4: LlmClient yields raw strings in stream mode
                if chunk_text:
                    full_response += chunk_text
                    await self.send_message(
                        target="broadcast",
                        type=MessageType.NARRATIVE_CHUNK,
                        content={"content": chunk_text, "is_final": False},
                        correlation_id=message.id # type: ignore
                    )

            if not full_response: full_response = "..."
            
            await self.send_message(target="broadcast", type=MessageType.NARRATIVE_TEXT, content=full_response, correlation_id=message.id) # type: ignore            
            
            response_msg = HLinkMessage(
                type=MessageType.NARRATIVE_TEXT,
                sender=Sender(agent_id=self.config.name, role=self.config.role),
                recipient=Recipient(target="broadcast"),
                payload=Payload(content=full_response)
            )
            self.ctx.history.append(response_msg)
            logger.info(f"FLOW_TRACE: Process COMPLETE for {self.config.name}.")
            
            # STORY 17.3: Silent update of tokens at the end
            try:
                await self.send_message(
                    target="broadcast", 
                    type=MessageType.SYSTEM_STATUS_UPDATE, 
                    content={
                        "status": "idle", 
                        "mood": "neutral",
                        "prompt_tokens": self.ctx.prompt_tokens,
                        "completion_tokens": self.ctx.completion_tokens,
                        "total_tokens": self.ctx.total_tokens
                    }
                )
            except Exception:
                pass
            return

        except Exception as e:
            logger.error(f"AGENT {self.config.name}: Crash during _process_narrative: {e}", exc_info=True)
            await self.send_message(target="broadcast", type=MessageType.NARRATIVE_TEXT, content=f"Désolée, mon système a eu une petite défaillance technique... 💋 (Erreur: {str(e)})")
            await self.send_message(target="broadcast", type=MessageType.SYSTEM_STATUS_UPDATE, content={"status": "idle", "mood": "error"})

    def _assemble_payload(self, current_message: HLinkMessage) -> list[dict[str, str]]:
        """Constructs the LLM message list with system instructions, persona prompt and history."""
        payload = []
        
        # 1. Load Global System Instructions (Story 11.4 Enhancement)
        system_instructions = ""
        try:
            import yaml
            # Look for config relative to the project root
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../config/prompts.yaml"))
            if os.path.exists(config_path):
                with open(config_path) as f:
                    config_data = yaml.safe_load(f)
                    system_instructions = config_data.get('system_instructions', "")
        except Exception as e:
            logger.warning(f"Failed to load global system instructions: {e}")

        # 2. Combine System Instructions + Agent Persona
        full_system_prompt = f"{system_instructions}\n\nYOUR SPECIFIC PERSONA:\n{self.system_prompt}"
        payload.append({"role": "system", "content": full_system_prompt})
        
        # 3. History (Context) - Last 10 messages max
        # Filter out the current message if it's already in history to avoid duplication
        recent_history = [m for m in self.ctx.history if m.id != current_message.id][-10:]
        
        for msg in recent_history:
            if msg.type == MessageType.NARRATIVE_TEXT:
                role = "assistant" if msg.sender.agent_id == self.config.name else "user"
                content = str(msg.payload.content)
                # STORY 17.4: Never send empty content to LLM in history
                if not content or content.strip() == "":
                    if role == "assistant":
                        content = "[Action technique effectuée]"
                    else:
                        continue # Skip empty user messages
                payload.append({"role": role, "content": content})
            elif msg.type == MessageType.AGENT_INTERNAL_NOTE:
                # Add internal notes as system observations
                payload.append({"role": "system", "content": f"[INTERNAL NOTE from {msg.sender.agent_id}]: {msg.payload.content}"})
        
        # 3. Current User Input
        payload.append({"role": "user", "content": str(current_message.payload.content)})
        
        return payload

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
