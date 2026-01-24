import asyncio
import logging
import json
import inspect
import os
from functools import wraps
from typing import Dict, Any, Callable, Optional, List
from uuid import uuid4

from src.infrastructure.redis import RedisClient
from src.infrastructure.llm import LlmClient
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload, Priority

logger = logging.getLogger(__name__)

class AgentContext:
    """Isolates the agent's state and local history."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.state: Dict[str, Any] = {}
        self.history: list[HLinkMessage] = []

    def update_state(self, key: str, value: Any):
        self.state[key] = value

    def get_state(self, key: str) -> Optional[Any]:
        return self.state.get(key)

class BaseAgent:
    """Generic base class for all specialized agents."""
    def __init__(self, config: AgentConfig, redis_client: RedisClient, llm_client: LlmClient, surreal_client: Optional[Any] = None):
        self.config = config
        self.redis = redis_client
        self.llm = llm_client
        self.surreal = surreal_client
        self.ctx = AgentContext(self.config.name)
        self.command_handlers: Dict[str, Callable] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._setup_default_handlers()
        self._setup_default_tools()

    def _setup_default_tools(self):
        """Register tools available to all agents."""
        if self.surreal:
            self.tool("Recall relevant past interactions or facts using a semantic query")(self.recall_memory)
        
        self.tool("Send a private internal note to another agent. This is not visible to the user.")(self.send_internal_note)

    async def recall_memory(self, query: str) -> str:
        """Semantic search tool."""
        if not self.surreal:
            return "Memory system is currently unavailable."
        
        try:
            embedding = await self.llm.get_embedding(query)
            if not embedding:
                return "Failed to process search query."
            
            results = await self.surreal.semantic_search(embedding, limit=3)
            if not results:
                return "No relevant memories found."
            
            # Format results for the agent
            memories = []
            for r in results:
                sender = r.get('sender', {}).get('agent_id', 'unknown')
                content = r.get('payload', {}).get('content', '')
                timestamp = r.get('timestamp', '')
                memories.append(f"[{timestamp}] {sender}: {content}")
            
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
        
        await self.redis.publish(f"agent:{target_agent}", note_msg)
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
                if param.annotation == int: param_type = "integer"
                if param.annotation == bool: param_type = "boolean"
                
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

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Returns the list of tools in OpenAI format."""
        return [t["schema"] for t in self.tools.values()]

    @property
    def system_prompt(self) -> str:
        """Returns the effective system prompt."""
        return self.config.prompt or f"You are {self.config.name}, a {self.config.role}."

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
        channel = f"agent:{self.config.name}"
        broadcast_channel = "agent:broadcast"
        logger.info(f"Agent {self.config.name} starting. Listening on {channel} and {broadcast_channel}")
        
        # Subscribe to own channel
        asyncio.create_task(self.redis.subscribe(channel, self.on_message))
        # Subscribe to broadcast channel
        asyncio.create_task(self.redis.subscribe(broadcast_channel, self.on_message))

    async def on_message(self, message: HLinkMessage):
        """Core message processing loop."""
        logger.info(f"Agent {self.config.name} received message of type {message.type}")
        
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
            await self._process_command(message)
        elif message.type == MessageType.NARRATIVE_TEXT:
            await self._process_narrative(message)

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
                    correlation_id=message.id
                )
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                await self.send_message(
                    target=message.sender.agent_id,
                    type=MessageType.EXPERT_RESPONSE,
                    content={"status": "error", "error": str(e)},
                    correlation_id=message.id
                )
            finally:
                await self.send_message(target="broadcast", type=MessageType.SYSTEM_STATUS_UPDATE, content={"status": "idle", "mood": "neutral"})
        else:
            logger.warning(f"Unknown command '{cmd_name}' for agent {self.config.name}")

    async def _process_narrative(self, message: HLinkMessage):
        """Handles narrative input using LLM streaming and tools."""
        logger.info(f"Agent {self.config.name} starts thinking...")
        
        await self.send_message(target="broadcast", type=MessageType.SYSTEM_LOG, content=f"Agent {self.config.name} is processing input...")
        await self.send_message(target="broadcast", type=MessageType.SYSTEM_STATUS_UPDATE, content={"status": "thinking", "mood": "pensive"})

        try:
            messages = self._assemble_payload(message)
            tools_schema = self.get_tools_schema()

            logger.info(f"DEBUG: Sending payload to LLM: {messages[-1]}") # Log last message only for brevity

            # Step 1: Check for tool calls (Non-streaming for safety)
            response = await self.llm.get_completion(
                messages, 
                stream=False, 
                tools=tools_schema if tools_schema else None,
                return_full_object=True
            )
            
            logger.info(f"DEBUG: LLM Response received: {type(response)}")

            # Handle potential API errors (if response is string)
            if isinstance(response, str):
                    logger.error(f"DEBUG: LLM returned string error: {response}")
                    await self.send_message(target="broadcast", type=MessageType.NARRATIVE_TEXT, content=response)
                    await self.send_message(target="broadcast", type=MessageType.SYSTEM_STATUS_UPDATE, content={"status": "idle", "mood": "neutral"})
                    return

            choice = response.choices[0]
            
            # Step 2: Handle Tool Calls
            if choice.message.tool_calls:
                logger.info(f"Agent {self.config.name} decided to use tools: {len(choice.message.tool_calls)}")
                
                # Add assistant's tool request to history
                messages.append(choice.message)
                
                # Execute tools
                tool_results = await self._execute_tool_calls(choice.message.tool_calls)
                
                # Add tool results to history
                messages.extend(tool_results)
                
                # Step 3: Get final response with new context (Streaming)
                logger.info("DEBUG: Requesting final stream after tools...")
                generator = await self.llm.get_completion(messages, stream=True)
            else:
                content = choice.message.content
                logger.info(f"DEBUG: Simple response content: {content[:50]}...")
                
                # Direct Send (No Streaming loop needed for simple response)
                await self.send_message(target="broadcast", type=MessageType.NARRATIVE_TEXT, content=content)
                
                response_msg = HLinkMessage(
                    type=MessageType.NARRATIVE_TEXT,
                    sender=Sender(agent_id=self.config.name, role=self.config.role),
                    recipient=Recipient(target="broadcast"),
                    payload=Payload(content=content)
                )
                self.ctx.history.append(response_msg)
                await self.send_message(target="broadcast", type=MessageType.SYSTEM_STATUS_UPDATE, content={"status": "idle", "mood": "neutral"})
                return

            # Handle Streaming Response (from Tool result or fallback)
            full_response = ""
            correlation_id = message.id

            logger.info("DEBUG: Starting stream iteration...")
            async for chunk in generator:
                full_response += chunk
                await self.send_message(
                    target="broadcast",
                    type=MessageType.NARRATIVE_CHUNK,
                    content={"content": chunk, "is_final": False},
                    correlation_id=correlation_id
                )
            logger.info("DEBUG: Stream finished.")

            await self.send_message(
                target="broadcast",
                type=MessageType.NARRATIVE_TEXT,
                content=full_response,
                correlation_id=correlation_id
            )
            
            response_msg = HLinkMessage(
                type=MessageType.NARRATIVE_TEXT,
                sender=Sender(agent_id=self.config.name, role=self.config.role),
                recipient=Recipient(target="broadcast"),
                payload=Payload(content=full_response)
            )
            self.ctx.history.append(response_msg)
            logger.info(f"Agent {self.config.name} finished response.")
            await self.send_message(target="broadcast", type=MessageType.SYSTEM_STATUS_UPDATE, content={"status": "idle", "mood": "neutral"})

        except Exception as e:
            logger.error(f"CRITICAL AGENT ERROR: {e}", exc_info=True)
            await self.send_message(target="broadcast", type=MessageType.SYSTEM_LOG, content=f"Agent Error: {e}")
            await self.send_message(target="broadcast", type=MessageType.SYSTEM_STATUS_UPDATE, content={"status": "error", "mood": "confused"})

    async def _execute_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            if function_name in self.tools:
                logger.info(f"Executing tool {function_name}")
                handler = self.tools[function_name]["handler"]
                try:
                    result = await handler(**arguments)
                    results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(result)
                    })
                except Exception as e:
                    results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": f"Error: {str(e)}"
                    })
        return results

    def _assemble_payload(self, current_message: HLinkMessage) -> List[Dict[str, str]]:
        """Constructs the LLM message list with system instructions, persona prompt and history."""
        payload = []
        
        # 1. Load Global System Instructions (Story 11.4 Enhancement)
        system_instructions = ""
        try:
            import yaml
            # Look for config relative to the project root
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../config/prompts.yaml"))
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    system_instructions = config_data.get('system_instructions', "")
        except Exception as e:
            logger.warning(f"Failed to load global system instructions: {e}")

        # 2. Combine System Instructions + Agent Persona
        full_system_prompt = f"{system_instructions}\n\nYOUR SPECIFIC PERSONA:\n{self.system_prompt}"
        payload.append({"role": "system", "content": full_system_prompt})
        
        # 3. History (Context) - Last 10 messages max
        recent_history = self.ctx.history[-10:]
        for msg in recent_history:
            if msg.type == MessageType.NARRATIVE_TEXT:
                role = "assistant" if msg.sender.agent_id == self.config.name else "user"
                payload.append({"role": role, "content": str(msg.payload.content)})
            elif msg.type == MessageType.AGENT_INTERNAL_NOTE:
                # Add internal notes as system observations
                payload.append({"role": "system", "content": f"[INTERNAL NOTE from {msg.sender.agent_id}]: {msg.payload.content}"})
        
        # 3. Current User Input
        payload.append({"role": "user", "content": str(current_message.payload.content)})
        
        return payload

    async def send_message(self, target: str, type: MessageType, content: Any, correlation_id: Optional[str] = None):
        """Sends a structured H-Link message."""
        channel = "broadcast" if target == "broadcast" else f"agent:{target}"
        
        msg = HLinkMessage(
            type=type,
            sender=Sender(agent_id=self.config.name, role=self.config.role),
            recipient=Recipient(target=target),
            payload=Payload(content=content),
            metadata={"correlation_id": correlation_id} if correlation_id else {}
        )
        
        await self.redis.publish(channel, msg)
