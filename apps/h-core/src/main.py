import asyncio
import json
import logging
import os
import signal
import datetime
import sys
from typing import Any, List, Optional

# Add agents path to sys.path
sys.path.insert(0, os.getenv("AGENTS_PATH", "/app/agents"))

from src.domain.memory import MemoryConsolidator
from src.infrastructure.llm import LlmClient
from src.infrastructure.plugin_loader import AgentRegistry, PluginLoader
from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender
from src.services.visual.dreamer import Dreamer
from src.services.visual.manager import AssetManager
from src.services.visual.provider import NanoBananaProvider, GoogleImagenProvider, ImagenV2Provider
from src.services.visual.service import VisualImaginationService
from src.services.chat.commands import CommandHandler
from src.utils.privacy import PrivacyFilter
from src.features.admin.token_tracking import TokenTrackingService
from src.features.admin.agent_management import AgentManagementService
from src.features.admin.agent_config import AgentConfigService
from src.features.admin.agent_creation import AgentCreationService
from src.features.home.spatial.rooms import RoomService
from src.features.home.spatial.location import LocationService
from src.features.home.spatial.mobile import MobileLocationService
from src.features.home.spatial.exterior import ExteriorService
try:
    from electra.drivers.ha_client import HaClient
except ImportError:
    logger.warning("HaClient not found in electra.drivers, using fallback mock")
    class HaClient:
        async def get_state(self, *args, **kwargs): return "off"
        async def toggle(self, *args, **kwargs): pass

# Configure base logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger("H-CORE")

class RedisLogHandler(logging.Handler):
    """Broadcasts logs to Redis for UI visibility, with loop protection."""
    def __init__(self, redis_client: RedisClient):
        super().__init__()
        self.redis = redis_client
        self._is_emitting = False
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()

    def emit(self, record):
        # Prevent infinite logging loops
        if self._is_emitting or not self.loop.is_running():
            return
            
        try:
            self._is_emitting = True
            msg_str = self.format(record)
            h_msg = HLinkMessage(
                type="system.log",
                sender=Sender(agent_id="core", role="system"),
                recipient=Recipient(target="broadcast"),
                payload=Payload(content=msg_str)
            )
            # Use call_soon_threadsafe to be 100% sure it hits the loop
            asyncio.run_coroutine_threadsafe(
                self.redis.publish_event("system_stream", h_msg.model_dump(mode='json')), 
                self.loop
            )
        except Exception:
            pass
        finally:
            self._is_emitting = False

class HaremOrchestrator:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.privacy_filter = PrivacyFilter()
        self.sleep_trigger_event = asyncio.Event()
        self.stop_event = asyncio.Event()
        
        # Core Infrastructure
        self.redis = RedisClient(host=os.getenv("REDIS_HOST", "localhost"))
        self.surreal = SurrealDbClient(
            url=os.getenv("SURREALDB_URL", "ws://surrealdb:8000/rpc"),
            user=os.getenv("SURREALDB_USER", "root"),
            password=os.getenv("SURREALDB_PASS", "root")
        )
        self.llm = LlmClient()
        self.agent_registry = AgentRegistry()
        
        # Services (Initialized in setup)
        self.visual_service: Optional[VisualImaginationService] = None
        self.consolidator: Optional[MemoryConsolidator] = None
        self.dreamer: Optional[Dreamer] = None
        self.command_handler: Optional[CommandHandler] = None
        self.ha_client: Optional[HaClient] = None
        self.plugin_loader: Optional[PluginLoader] = None
        self.token_tracking_service: Optional[TokenTrackingService] = None
        self.agent_management_service: Optional[AgentManagementService] = None
        self.agent_config_service: Optional[AgentConfigService] = None
        self.agent_creation_service: Optional[AgentCreationService] = None
        self.provider_config_service: Optional[Any] = None  # Story 7.5
        self.location_service: Optional[LocationService] = None
        self.mobile_location_service: Optional[MobileLocationService] = None
        self.exterior_service: Optional[ExteriorService] = None
        
        self.tasks: List[asyncio.Task] = []

    async def setup(self):
        """Sequential initialization of all components."""
        logger.info("ORCHESTRATOR: Starting setup...")
        
        # 1. Connect to Infrastructure
        if not await self.redis.connect():
            raise RuntimeError("Failed to connect to Redis")
        await self.surreal.connect()
        
        # 2. Attach Redis Log Handler
        log_handler = RedisLogHandler(self.redis)
        log_handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
        logging.getLogger().addHandler(log_handler)
        
        # 3. Initialize Services
        self.ha_client = HaClient()
        
        # Visual Provider Selection
        provider_type = os.getenv("VISUAL_PROVIDER", "nanobanana").lower()
        if provider_type == "google":
            provider = GoogleImagenProvider()
        elif provider_type == "imagen-v2":
            provider = ImagenV2Provider()
        else:
            provider = NanoBananaProvider()
            
        asset_manager = AssetManager(self.surreal)
        self.visual_service = VisualImaginationService(
            provider, asset_manager, self.llm, self.redis
        )
        
        self.consolidator = MemoryConsolidator(self.surreal, self.llm, self.redis)
        self.dreamer = Dreamer(self.ha_client, self.visual_service)
        self.command_handler = CommandHandler(self.redis, self.visual_service, self.surreal)
        
        # Admin Services
        self.token_tracking_service = TokenTrackingService(self.surreal)
        await self.token_tracking_service.initialize()
        
        self.agent_management_service = AgentManagementService(self.redis, self.agent_registry)
        
        self.agent_config_service = AgentConfigService(self.surreal, self.agent_registry)
        await self.agent_config_service.initialize()
        
        # 7. Initialize Provider Config Service (Story 7.5)
        from src.features.admin.provider_config import ProviderConfigService
        self.provider_config_service = ProviderConfigService(self.agent_config_service)
        
        # Room Service
        self.room_service = RoomService(self.surreal, self.agent_registry)
        await self.room_service.initialize()
        
        # Location Service
        self.location_service = LocationService(self.surreal, self.room_service)
        await self.location_service.initialize()
        
        # Exterior Service (Story 9.4)
        self.exterior_service = ExteriorService(self.location_service)
        await self.exterior_service.initialize()
        
        # Mobile Location Service
        self.mobile_location_service = MobileLocationService(self.location_service, exterior_service=self.exterior_service)
        await self.mobile_location_service.initialize()
        
        # 5. Initialize Agent Creation Service
        self.agent_creation_service = AgentCreationService(
            self.surreal, self.plugin_loader, self.agent_registry, self.room_service
        )
        
        # 4. Load Plugins
        self.plugin_loader = PluginLoader(
            os.getenv("AGENTS_PATH", "/app/agents"),
            self.agent_registry, self.redis, self.llm, self.surreal
        )
        self.plugin_loader.visual_service = self.visual_service
        self.plugin_loader.token_tracking_service = self.token_tracking_service
        await self.plugin_loader.start()
        
        # 6. Load agents from database on startup (Story 7.4 AC2)
        await self._load_agents_from_db()
        
        # FIX: Clear old stream messages to prevent replay on restart
        try:
            # Delete and recreate the consumer group to start fresh
            try:
                await self.redis.client.xgroup_destroy("system_stream", "h-core")
                logger.info("ROUTER: Destroyed old consumer group")
            except:
                pass
            await self.redis.client.xtrim("system_stream", 0)  # Keep only 0 messages
            logger.info("ROUTER: Cleared old stream messages to prevent replay")
        except Exception as e:
            logger.warning(f"ROUTER: Could not clear stream: {e}")
        
        logger.info("ORCHESTRATOR: Setup complete.")

    async def message_router(self):
        """Central message routing using Redis Streams."""
        logger.info("ROUTER: Listening on 'system_stream' group 'h-core'...")
        
    async def handle_system_message(self, data: dict):
        """Processes incoming events from the Redis system stream."""
        try:
            # Reconstruct HLinkMessage from flattened dict
            # Fix: If it's a log or update, it might already be valid
            msg, error = HLinkMessage.validate_message(data)
            
            if error:
                # Try unwrapping if it comes from bridge
                if "data" in data and isinstance(data["data"], str):
                    try:
                        inner_data = json.loads(data["data"])
                        return await self.handle_system_message(inner_data)
                    except: pass
                logger.debug(f"ROUTER: Skipping non-HLink or invalid message: {error}")
                return
            
            # 0. Handle Admin Agent Control Messages (Story 7.2)
            if msg.type in ["admin.agent.enable", "admin.agent.disable"]:
                if self.agent_management_service:
                    agent_id = msg.recipient.target
                    if msg.type == "admin.agent.enable":
                        await self.agent_management_service.enable_agent(agent_id)
                        logger.info(f"ROUTER: Enabled agent {agent_id}")
                    elif msg.type == "admin.agent.disable":
                        await self.agent_management_service.disable_agent(agent_id)
                        logger.info(f"ROUTER: Disabled agent {agent_id}")
                return
            
            # 0.1 Handle Admin Agent Config Messages (Story 7.3)
            if msg.type == "admin.agent.config":
                if self.agent_config_service:
                    agent_id = msg.recipient.target
                    content = msg.payload.content if isinstance(msg.payload.content, dict) else {}
                    parameters = content.get("parameters", {})
                    
                    result = await self.agent_config_service.save_config(agent_id, parameters)
                    
                    response_msg = HLinkMessage(
                        type="admin.agent.config_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content=result)
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                    logger.info(f"ROUTER: Config saved for agent {agent_id}")
                return
            
            if msg.type == "admin.agent.get_config":
                if self.agent_config_service:
                    agent_id = msg.recipient.target
                    result = await self.agent_config_service.get_config(agent_id)
                    
                    response_msg = HLinkMessage(
                        type="admin.agent.config_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content=result)
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                return
            
            if msg.type == "admin.agent.list_configs":
                if self.agent_config_service:
                    result = await self.agent_config_service.list_configs()
                    
                    response_msg = HLinkMessage(
                        type="admin.agent.config_list_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content=result)
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                return
            
            # 0.3 Handle LLM Connection Test (Story 7.5)
            if msg.type == "admin.llm.test_connection":
                if self.provider_config_service:
                    content = msg.payload.content if isinstance(msg.payload.content, dict) else {}
                    
                    result = await self.provider_config_service.test_connection(
                        provider=content.get("provider", "ollama"),
                        model=content.get("model"),
                        base_url=content.get("base_url"),
                        api_key=content.get("api_key")
                    )
                    
                    response_msg = HLinkMessage(
                        type="admin.llm.test_connection_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content=result)
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                    logger.info(f"ROUTER: LLM test completed for provider {content.get('provider')}")
                return
            
            # 0.2 Handle Admin Agent Creation Messages (Story 7.4)
            if msg.type == "admin.agent.create":
                if self.agent_creation_service:
                    content = msg.payload.content if isinstance(msg.payload.content, dict) else {}
                    
                    from src.features.admin.agent_creation import AgentCreationPayload
                    try:
                        payload = AgentCreationPayload.model_validate(content)
                    except Exception as e:
                        response_msg = HLinkMessage(
                            type="admin.agent.create_response",
                            sender=Sender(agent_id="core", role="system"),
                            recipient=Recipient(target=msg.sender.agent_id),
                            payload=Payload(content={"success": False, "error": f"Invalid payload: {str(e)}"})
                        )
                        await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                        return
                    
                    result = await self.agent_creation_service.create_agent(payload)
                    
                    response_msg = HLinkMessage(
                        type="admin.agent.create_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content=result)
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                    logger.info(f"ROUTER: Agent creation result for {payload.name}: {result}")
                return
            
            if msg.type == "admin.agent.list":
                if self.agent_creation_service:
                    result = await self.agent_creation_service.list_agents_from_db()
                    
                    response_msg = HLinkMessage(
                        type="admin.agent.list_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content={"success": True, "agents": result})
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                return
            
            if msg.type == "admin.agent.delete":
                if self.agent_creation_service:
                    agent_id = msg.recipient.target
                    result = await self.agent_creation_service.delete_agent(agent_id)
                    
                    response_msg = HLinkMessage(
                        type="admin.agent.delete_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content=result)
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                    logger.info(f"ROUTER: Agent deletion result for {agent_id}: {result}")
                return
            
            # Room Management (Story 9.1)
            if msg.type == "admin.room.create":
                if self.room_service:
                    content = msg.payload.content if isinstance(msg.payload.content, dict) else {}
                    result = await self.room_service.create_room(
                        room_id=content.get("room_id"),
                        name=content.get("name"),
                        type=content.get("type", "generic"),
                        description=content.get("description")
                    )
                    response_msg = HLinkMessage(
                        type="admin.room.create_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content=result)
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                return
            
            if msg.type == "admin.room.list":
                if self.room_service:
                    rooms = await self.room_service.list_rooms()
                    response_msg = HLinkMessage(
                        type="admin.room.list_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content={"success": True, "rooms": rooms})
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                return
            
            if msg.type == "admin.room.assign":
                if self.room_service:
                    agent_id = msg.recipient.target
                    content = msg.payload.content if isinstance(msg.payload.content, dict) else {}
                    room_id = content.get("room_id")
                    
                    result = await self.room_service.assign_agent_to_room(agent_id, room_id)
                    
                    response_msg = HLinkMessage(
                        type="admin.room.assign_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content=result)
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                    logger.info(f"ROUTER: Room assignment for agent {agent_id}: {result}")
                return
            
            if msg.type == "admin.room.get_agent_room":
                if self.room_service:
                    agent_id = msg.recipient.target
                    room = await self.room_service.get_agent_room(agent_id)
                    
                    response_msg = HLinkMessage(
                        type="admin.room.agent_room_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content={"success": True, "room": room})
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                return
            
            # Mobile Location (Story 9.3)
            if msg.type == "mobile.client.register":
                if self.mobile_location_service:
                    content = msg.payload.content if isinstance(msg.payload.content, dict) else {}
                    client_id = content.get("client_id")
                    agent_id = content.get("agent_id")
                    
                    if not client_id or not agent_id:
                        response_msg = HLinkMessage(
                            type="mobile.client.register_response",
                            sender=Sender(agent_id="core", role="system"),
                            recipient=Recipient(target=msg.sender.agent_id),
                            payload=Payload(content={"success": False, "error": "client_id and agent_id required"})
                        )
                        await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                        return
                    
                    client_info = await self.mobile_location_service.register_client(client_id, agent_id)
                    response_msg = HLinkMessage(
                        type="mobile.client.register_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content={"success": True, "client_id": client_info.client_id, "agent_id": client_info.agent_id})
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                    logger.info(f"ROUTER: Mobile client {client_id} registered for agent {agent_id}")
                return
            
            if msg.type == "mobile.location.update":
                if self.mobile_location_service:
                    content = msg.payload.content if isinstance(msg.payload.content, dict) else {}
                    client_id = content.get("client_id")
                    
                    try:
                        from src.features.home.spatial.mobile.models import MobileLocationUpdate
                        location_data = content.get("location", {})
                        location = MobileLocationUpdate.model_validate(location_data)
                    except Exception as e:
                        response_msg = HLinkMessage(
                            type="mobile.location.update_response",
                            sender=Sender(agent_id="core", role="system"),
                            recipient=Recipient(target=msg.sender.agent_id),
                            payload=Payload(content={"success": False, "error": f"Invalid location data: {str(e)}"})
                        )
                        await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                        return
                    
                    result = await self.mobile_location_service.handle_location_update(client_id, location)
                    response_msg = HLinkMessage(
                        type="mobile.location.update_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content=result)
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                    logger.info(f"ROUTER: Mobile location update from {client_id}: {result}")
                return
            
            if msg.type == "mobile.client.disconnect":
                if self.mobile_location_service:
                    content = msg.payload.content if isinstance(msg.payload.content, dict) else {}
                    client_id = content.get("client_id")
                    
                    if not client_id:
                        response_msg = HLinkMessage(
                            type="mobile.client.disconnect_response",
                            sender=Sender(agent_id="core", role="system"),
                            recipient=Recipient(target=msg.sender.agent_id),
                            payload=Payload(content={"success": False, "error": "client_id required"})
                        )
                        await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                        return
                    
                    client_info = await self.mobile_location_service.handle_disconnect(client_id)
                    response_msg = HLinkMessage(
                        type="mobile.client.disconnect_response",
                        sender=Sender(agent_id="core", role="system"),
                        recipient=Recipient(target=msg.sender.agent_id),
                        payload=Payload(content={
                            "success": True,
                            "client_id": client_id,
                            "last_location": {
                                "latitude": client_info.last_latitude if client_info else None,
                                "longitude": client_info.last_longitude if client_info else None,
                                "room_id": client_info.last_room_id if client_info else None
                            } if client_info else None
                        })
                    )
                    await self.redis.publish_event("system_stream", response_msg.model_dump(mode='json'))
                    logger.info(f"ROUTER: Mobile client {client_id} disconnected, last location preserved")
                return
            
            # ... (rest of the routing logic)
            
            # 1. Handle Sleep Signal
            if msg.type == MessageType.SYSTEM_STATUS_UPDATE:
                content = msg.payload.content
                if isinstance(content, dict) and content.get("status") == "SLEEP_START":
                    logger.info("ROUTER: Received SLEEP_START signal.")
                    self.sleep_trigger_event.set()

            # 2. Persist Narrative/Visual messages
            if msg.type in [MessageType.NARRATIVE_TEXT, MessageType.EXPERT_RESPONSE, MessageType.VISUAL_ASSET, MessageType.USER_MESSAGE]:
                data_dump = msg.model_dump(mode='json')
                if isinstance(data_dump.get("payload", {}).get("content"), str):
                    redacted, _ = self.privacy_filter.redact(data_dump["payload"]["content"])
                    data_dump["payload"]["content"] = redacted
                
                data_dump["agent_id"] = msg.sender.agent_id
                await self.surreal.persist_message(data_dump)

            # 3. Route User Messages to Agents
            if msg.type == MessageType.USER_MESSAGE:
                target = msg.recipient.target
                
                # BUG FIX: Don't route messages to "user" - prevents echo
                if target == "user":
                    logger.info(f"ROUTER: Dropping message to 'user' - prevents echo")
                    return
                    
                # Story 7.2 AC2: Check if target agent is active
                if target != "broadcast" and target != "all":
                    agent = self.agent_registry.agents.get(target)
                    if agent and not agent.is_active:
                        unavailable_msg = HLinkMessage(
                            type=MessageType.NARRATIVE_TEXT,
                            sender=Sender(agent_id="system", role="system"),
                            recipient=Recipient(target=msg.sender.agent_id),
                            payload=Payload(content=f"Désolée, l'agent '{target}' est actuellement indisponible. Veuillez réessayer plus tard.")
                        )
                        await self.redis.publish_event("system_stream", unavailable_msg.model_dump(mode='json'))
                        logger.info(f"ROUTER: User message to disabled agent {target} - sent unavailable message")
                        return
                logger.info(f"ROUTER: Routing message to agent {target}")
                channel = f"agent:{target}"
                await self.redis.publish(channel, msg)

            # 4. Handle Commands & Narrative Routing
            elif msg.type == MessageType.NARRATIVE_TEXT:
                content = str(msg.payload.content)
                if content.startswith("/"):
                    await self.command_handler.execute(content, msg)
                else:
                    # STORY 14.1 FIX: Route standard text to agents
                    target = msg.recipient.target
                    
                    # BUG FIX: Don't route narrative to "user" - prevents echo
                    if target == "user":
                        logger.info(f"ROUTER: Dropping narrative to 'user' - prevents echo")
                        return
                        
                    # Story 7.2 AC2: Check if target agent is active
                    if target != "broadcast" and target != "all":
                        agent = self.agent_registry.agents.get(target)
                        if agent and not agent.is_active:
                            unavailable_msg = HLinkMessage(
                                type=MessageType.NARRATIVE_TEXT,
                                sender=Sender(agent_id="system", role="system"),
                                recipient=Recipient(target=msg.sender.agent_id),
                                payload=Payload(content=f"Désolée, l'agent '{target}' est actuellement indisponible. Veuillez réessayer plus tard.")
                            )
                            await self.redis.publish_event("system_stream", unavailable_msg.model_dump(mode='json'))
                            logger.info(f"ROUTER: Narrative to disabled agent {target} - sent unavailable message")
                            return
                    logger.info(f"ROUTER: Routing narrative message to agent {target}")
                    channel = "agent:broadcast" if target in ["broadcast", "all"] else f"agent:{target}"
                    await self.redis.publish(channel, msg)
                
            elif msg.type == MessageType.EXPERT_COMMAND:
                payload = msg.payload.content
                if isinstance(payload, dict):
                    cmd = payload.get("command")
                    args = payload.get("args", "")
                    if msg.recipient.target == "outfit":
                        await self.command_handler.execute(f"/outfit {cmd} {args}", msg)
                    elif cmd in self.command_handler.commands:
                        await self.command_handler.execute(f"/{cmd} {args}", msg)
        except Exception as e:
            logger.error(f"ROUTER: Error processing message: {e}")

    async def _load_agents_from_db(self):
        if not self.agent_creation_service:
            return
        try:
            db_agents = await self.agent_creation_service.list_agents_from_db()
            loaded_agents = set(self.agent_registry.agents.keys())
            
            for agent_data in db_agents:
                agent_name = agent_data.get("name")
                if agent_name and agent_name not in loaded_agents:
                    agents_folder = agent_data.get("agents_folder")
                    if agents_folder:
                        success = await self.plugin_loader.load_agent_from_folder(agents_folder)
                        if success:
                            logger.info(f"ORCHESTRATOR: Loaded agent {agent_name} from database")
        except Exception as e:
            logger.error(f"ORCHESTRATOR: Failed to load agents from database: {e}")

    async def message_router(self):
        """Central message routing using Redis Streams."""
        logger.info("ROUTER: Listening on 'system_stream' group 'h-core'...")
        await self.redis.listen_stream("system_stream", "h-core", os.getenv("HOSTNAME", "core-1"), self.handle_system_message)

    async def sleep_cycle_worker(self):
        """Background worker for memory consolidation and maintenance."""
        logger.info("WORKER: Sleep cycle worker active.")
        last_hourly_run = 0
        last_daily_run_date = None
        
        while not self.stop_event.is_set():
            try:
                now = datetime.datetime.now()
                today = now.date()
                
                # Forced trigger or Hourly run
                if self.sleep_trigger_event.is_set() or (now.timestamp() - last_hourly_run >= 3600):
                    logger.info("WORKER: Executing memory consolidation...")
                    await self.consolidator.consolidate()
                    last_hourly_run = now.timestamp()
                    self.sleep_trigger_event.clear()
                
                # Daily Maintenance (3 AM)
                if now.hour == 3 and last_daily_run_date != today:
                    logger.info("WORKER: Executing daily deep maintenance...")
                    await self.consolidator.apply_decay()
                    await self.dreamer.prepare_daily_assets()
                    last_daily_run_date = today
                    
            except Exception as e:
                logger.error(f"WORKER: Sleep cycle error: {e}", exc_info=True)
            
            await asyncio.sleep(60)

    async def status_heartbeat(self):
        """Regularly publish system health and brain status to stream."""
        while not self.stop_event.is_set():
            try:
                # 1. Redis/Core Health
                await self.redis.publish_event("system_stream", HLinkMessage(
                    type=MessageType.SYSTEM_STATUS_UPDATE,
                    sender=Sender(agent_id="core", role="system"),
                    recipient=Recipient(target="system"),
                    payload=Payload(content={"component": "redis", "status": "ok", "time": datetime.datetime.utcnow().isoformat()})
                ).model_dump(mode='json'))
                
                # 2. LLM Health
                await self.redis.publish_event("system_stream", HLinkMessage(
                    type=MessageType.SYSTEM_STATUS_UPDATE,
                    sender=Sender(agent_id="core", role="system"),
                    recipient=Recipient(target="system"),
                    payload=Payload(content={"component": "llm", "status": "ok"})
                ).model_dump(mode='json'))

                # 3. Agent Status (for Discovery)
                for agent_id, agent in self.agent_registry.agents.items():
                    await self.redis.publish_event("system_stream", HLinkMessage(
                        type=MessageType.SYSTEM_STATUS_UPDATE,
                        sender=Sender(agent_id=agent_id, role=agent.config.role),
                        recipient=Recipient(target="broadcast"),
                        payload=Payload(content={
                            "status": "idle", 
                            "active": agent.is_active,
                            "personified": agent.personified,
                            "commands": list(agent.command_handlers.keys()),
                            "total_tokens": agent.ctx.total_tokens
                        })
                    ).model_dump(mode='json'))

                # 4. Brain Capabilities
                await self.redis.publish_event("system_stream", HLinkMessage(
                    type=MessageType.SYSTEM_STATUS_UPDATE,
                    sender=Sender(agent_id="system", role="orchestrator"),
                    recipient=Recipient(target="system"),
                    payload=Payload(content={
                        "component": "brain", 
                        "status": "online", 
                        "commands": list(self.command_handler.commands.keys())
                    })
                ).model_dump(mode='json'))
            except Exception as e:
                logger.warning(f"HEARTBEAT: Failed: {e}")
            
            await asyncio.sleep(15) # Heartbeat faster for UI responsiveness

    async def run(self):
        """Main execution loop."""
        await self.setup()
        
        self.tasks = [
            asyncio.create_task(self.message_router()),
            asyncio.create_task(self.sleep_cycle_worker()),
            asyncio.create_task(self.status_heartbeat())
        ]
        
        logger.info("H-CORE: All systems operational.")
        await self.stop_event.wait()

    async def shutdown(self):
        """Graceful shutdown of all tasks and connections."""
        logger.info("SHUTDOWN: Commencing graceful exit...")
        self.stop_event.set()
        
        # Cancel tasks
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close connections
        if self.redis: await self.redis.disconnect()
        if self.surreal: await self.surreal.close()
        
        logger.info("SHUTDOWN: Complete. Goodbye.")

def main():
    orchestrator = HaremOrchestrator()
    
    # Signal handling
    def signal_handler():
        logger.warning("Caught stop signal!")
        asyncio.create_task(orchestrator.shutdown())

    for sig in (signal.SIGINT, signal.SIGTERM):
        orchestrator.loop.add_signal_handler(sig, signal_handler)

    try:
        orchestrator.loop.run_until_complete(orchestrator.run())
    except Exception as e:
        logger.critical(f"CRASH: {e}", exc_info=True)
    finally:
        orchestrator.loop.close()

if __name__ == "__main__":
    main()