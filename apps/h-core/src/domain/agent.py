import asyncio
import logging
import json
import inspect
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
    def __init__(self, config: AgentConfig, redis_client: RedisClient, llm_client: LlmClient):
        self.config = config
        self.redis = redis_client
        self.llm = llm_client
        self.ctx = AgentContext(self.config.name)
        self.command_handlers: Dict[str, Callable] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._setup_default_handlers()

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
        logger.info(f"Agent {self.config.name} starting. Listening on {channel}")
        asyncio.create_task(self.redis.subscribe(channel, self.on_message))

    async def on_message(self, message: HLinkMessage):
        """Core message processing loop."""
        logger.info(f"Agent {self.config.name} received message of type {message.type}")
        # 1. Store in history
        self.ctx.history.append(message)

        # 2. Routing logic
        if message.type == MessageType.EXPERT_COMMAND:
            await self._process_command(message)
        elif message.type == MessageType.NARRATIVE_TEXT:
            await self._process_narrative(message)
        
        # 3. Prevent infinite loops (TTL check could go here)

    async def _process_command(self, message: HLinkMessage):
        """Executes a requested tool/command."""
        cmd_name = message.payload.content.get("command") if isinstance(message.payload.content, dict) else str(message.payload.content)
        
        if cmd_name in self.command_handlers:
            logger.info(f"Agent {self.config.name} executing command: {cmd_name}")
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
        else:
            logger.warning(f"Unknown command '{cmd_name}' for agent {self.config.name}")

    async def _process_narrative(self, message: HLinkMessage):
        """Handles narrative input using LLM streaming and tools."""
        logger.info(f"Agent {self.config.name} starts thinking...")
        
        await self.send_message(target="broadcast", type=MessageType.SYSTEM_LOG, content=f"Agent {self.config.name} is processing input...")

        messages = self._assemble_payload(message)
        tools_schema = self.get_tools_schema()

        # Step 1: Check for tool calls (Non-streaming for safety)
        response = await self.llm.get_completion(
            messages, 
            stream=False, 
            tools=tools_schema if tools_schema else None,
            return_full_object=True
        )

        # Handle potential API errors (if response is string)
        if isinstance(response, str):
                await self.send_message(target="broadcast", type=MessageType.NARRATIVE_TEXT, content=response)
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
            generator = await self.llm.get_completion(messages, stream=True)
        else:
            content = choice.message.content
            await self.send_message(target="broadcast", type=MessageType.NARRATIVE_TEXT, content=content)
            
            response_msg = HLinkMessage(
                type=MessageType.NARRATIVE_TEXT,
                sender=Sender(agent_id=self.config.name, role=self.config.role),
                recipient=Recipient(target="broadcast"),
                payload=Payload(content=content)
            )
            self.ctx.history.append(response_msg)
            return

        # Handle Streaming Response (from Tool result or fallback)
        full_response = ""
        correlation_id = message.id

        async for chunk in generator:
            full_response += chunk
            await self.send_message(
                target="broadcast",
                type=MessageType.NARRATIVE_CHUNK,
                content={"content": chunk, "is_final": False},
                correlation_id=correlation_id
            )

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
        """Constructs the LLM message list with system prompt and history."""
        payload = []
        
        # 1. System Prompt (Identity)
        payload.append({"role": "system", "content": self.system_prompt})
        
        # 2. History (Context) - Last 10 messages max
        recent_history = self.ctx.history[-10:]
        for msg in recent_history:
            if msg.type == MessageType.NARRATIVE_TEXT:
                role = "assistant" if msg.sender.agent_id == self.config.name else "user"
                payload.append({"role": role, "content": str(msg.payload.content)})
        
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