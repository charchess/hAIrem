import asyncio
import json
import logging
import os
from uuid import UUID, uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketState

from infrastructure.redis import RedisClient
from infrastructure.surrealdb import SurrealDbClient
from models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender
from handlers.audio import handle_audio_message
from handlers.wakeword import handle_wakeword_message
from handlers.whisper import handle_whisper_request
from handlers.tts import handle_tts_request
from dependencies.auth import get_current_user, require_admin, validate_agent_id, TokenPayload
from services.voice import voice_profile_service
from services.voice_modulation import voice_modulation_service, EMOTION_CONFIGS
from services.prosody import prosody_service

# Logging setup
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="hAIrem Bridge")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
# Handle local vs docker paths
if os.path.exists("/app/static"):
    public_path = "/app/static"
else:
    # Local fallback relative to this file
    public_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../static"))

logger.info(f"Using static path: {public_path}")

redis_host = os.getenv("REDIS_HOST", "redis")
surreal_url = os.getenv("SURREALDB_URL", "ws://surrealdb:8000/rpc")

# Infrastructure Clients
redis_client = RedisClient(host=redis_host)
surreal_client = SurrealDbClient(
    url=surreal_url, user=os.getenv("SURREALDB_USER", "root"), password=os.getenv("SURREALDB_PASS", "root")
)

# --- Static Files ---
app.mount("/static", StaticFiles(directory=public_path), name="static")
app.mount("/agents", StaticFiles(directory="/app/agents"), name="agents")


@app.get("/", response_class=HTMLResponse)
async def root():
    with open(os.path.join(public_path, "index.html"), "r", encoding="utf-8") as f:
        return f.read()


# Global agent cache for the API
discovered_agents = {}


async def agent_discovery_worker():
    """Listens for agent status updates to populate discovered_agents using Streams."""
    logger.info("BRIDGE: Discovery worker started.")

    async def handler(data: dict):
        try:
            # STORY 14.1 FIX: Support both flat and nested HLink formats
            msg_type = data.get("type")
            sender = data.get("sender", {})
            payload = data.get("payload", {})

            # If sender or payload are strings (Redis Stream artifact), parse them
            if isinstance(sender, str):
                sender = json.loads(sender)
            if isinstance(payload, str):
                payload = json.loads(payload)

            if msg_type == MessageType.SYSTEM_STATUS_UPDATE:
                agent_id = sender.get("agent_id")
                # BUG FIX: Filter out system/core/user from agent discovery
                if agent_id in ["core", "system", "user"] or not agent_id:
                    return

                status_data = payload.get("content")
                if isinstance(status_data, dict):
                    discovered_agents[agent_id] = {
                        "id": agent_id,
                        "active": status_data.get("active", True),
                        "personified": status_data.get("personified", True),
                        "role": sender.get("role", "Agent"),
                        "commands": status_data.get("commands", []),
                        "total_tokens": status_data.get("total_tokens", 0),
                    }
                    logger.info(f"BRIDGE: Discovered agent {agent_id}")
        except Exception as e:
            logger.error(f"BRIDGE: Discovery error: {e}")

    await redis_client.listen_stream("system_stream", "h-bridge-discovery", os.getenv("HOSTNAME", "bridge-1"), handler)


# --- API Endpoints ---
@app.post("/api/test/seed-graph")
async def seed_graph(data: dict):
    """Injects test data into the graph."""
    if os.getenv("ENV") != "test" and not os.getenv("DEBUG"):
        return {"status": "error", "message": "Seeding only allowed in test/debug mode"}

    try:
        # 1. Subjects
        for sub in data.get("subjects", []):
            name = sub.get("name")
            if name:
                sid = f"subject:`{name.lower().replace(' ', '_')}`"
                await surreal_client._call(
                    "query",
                    f"INSERT INTO subject (id, name) VALUES ({sid}, $name) ON DUPLICATE KEY UPDATE name = $name;",
                    {"name": name},
                )

        # 2. Facts
        for fact in data.get("facts", []):
            await surreal_client.insert_graph_memory(fact)

        return {"status": "success", "message": "Graph seeded"}
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/test/reset-streams")
async def reset_streams(data: dict):
    """Purges Redis streams."""
    streams = data.get("streams", [])
    for s in streams:
        await redis_client.client.delete(s)
    return {"status": "success", "message": f"Reset {len(streams)} streams"}


@app.get("/api/agents")
async def get_agents():
    """Returns the list of agents discovered via Redis status updates."""
    return list(discovered_agents.values())


@app.get("/api/history")
async def get_history():
    if not surreal_client.client:
        return {"messages": [], "status": "connecting"}
    try:
        # STORY 13.1 FIX: Use new 'fact' table for history retrieval
        res = await surreal_client._call("query", "SELECT * FROM fact ORDER BY created_at DESC LIMIT 50;")
        messages = res[0].get("result", []) if isinstance(res[0], dict) else res
        return {"messages": messages, "status": "ok"}
    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}")
        return {"messages": [], "status": "error"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "h-bridge"}


@app.get("/api/debug/error")
async def trigger_debug_error():
    """Simulates a critical system error for UI testing."""
    msg = HLinkMessage(
        type=MessageType.SYSTEM_LOG,
        sender=Sender(agent_id="system", role="orchestrator"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="[ERROR] CRITICAL_SYSTEM_FAILURE: Debug error triggered via API"),
    )
    await redis_client.publish_event("system_stream", msg.model_dump())
    return {"status": "debug_error_sent"}


# --- WebSocket Bridge ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("New A2UI client connected.")

    # STORY 14.1 FIX: Send immediate confirmation to UI to unlock input
    await websocket.send_text(
        json.dumps(
            {
                "type": "system.status_update",
                "sender": {"agent_id": "bridge", "role": "gateway"},
                "recipient": {"target": "user"},
                "payload": {"content": {"component": "ws", "status": "ok"}},
            }
        )
    )

    # Also send a welcome log
    await websocket.send_text(
        json.dumps({"type": "system.log", "payload": {"content": "BRIDGE: Connexion établie. Système prêt."}})
    )

    async def redis_to_ws():
        if not redis_client.client:
            await redis_client.connect()

        async def handler(data: dict):
            try:
                if websocket.client_state != WebSocketState.CONNECTED:
                    return

                # STORY 14.1 FIX: Absolute mapping for UI compatibility
                msg_type = data.get("type")

                # Force status update format for Dashboard
                if msg_type == "system.status_update" or msg_type == MessageType.SYSTEM_STATUS_UPDATE:
                    logger.info(f"BRIDGE: Relaying status update to UI")
                    await websocket.send_text(json.dumps(data))
                    return

                # Force log format for terminal
                if msg_type == "system.log" or msg_type == MessageType.SYSTEM_LOG:
                    content = data.get("payload", {}).get("content", str(data))
                    await websocket.send_text(json.dumps({"type": "system.log", "payload": {"content": str(content)}}))
                    return

                # Default relay
                await websocket.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"BRIDGE: WS relay error: {e}")

        # FIX: Use a FIXED group name instead of unique per connection
        # This prevents accumulation of thousands of consumer groups
        # Each new browser connection adds a new consumer to the same group
        fixed_group = "h-bridge-ws"
        consumer_id = f"ws-{uuid4().hex[:8]}"
        await redis_client.listen_stream("system_stream", fixed_group, consumer_id, handler)

    try:
        listen_task = asyncio.create_task(redis_to_ws())

        while True:
            data = await websocket.receive_text()
            try:
                raw_msg = json.loads(data)
                msg_type = raw_msg.get("type")

                # Route to appropriate handler based on message type
                if msg_type in ["user_audio", "audio_session_request", "audio_session_stop", "audio_session_status"]:
                    await handle_audio_message(websocket, raw_msg, redis_client)
                elif msg_type in ["wakeword_status_request", "wakeword_enable", "wakeword_disable"]:
                    await handle_wakeword_message(websocket, raw_msg, redis_client)
                elif msg_type in [
                    "whisper_session_start",
                    "whisper_session_end",
                    "whisper_audio_data",
                    "whisper_status",
                ]:
                    await handle_whisper_request(websocket, raw_msg, redis_client)
                elif msg_type == "tts_request":
                    await handle_tts_request(websocket, raw_msg, redis_client)
                else:
                    # Default HLink message handling for other types
                    if all(k in raw_msg for k in ["type", "sender", "recipient", "payload"]):
                        msg, error = HLinkMessage.validate_message(raw_msg)
                        if not error:
                            # STORY 14.1 FIX: Use mode='json' to ensure UUID/datetime are serialized
                            await redis_client.publish_event("system_stream", msg.model_dump(mode="json"))
                        else:
                            logger.error(f"Invalid WS message format: {error}")
                    else:
                        # Fallback for older or partial messages from UI
                        await redis_client.publish_event("system_stream", raw_msg)

            except Exception as e:
                logger.error(f"Error processing WS message: {e}")

    except WebSocketDisconnect:
        logger.info("A2UI client disconnected.")
        listen_task.cancel()
    except Exception as e:
        logger.error(f"WS Bridge Error: {e}")


def safe_json_dumps(obj):
    """Handles UUID and datetime for JSON serialization."""

    def helper(o):
        if isinstance(o, (UUID, datetime)):
            return str(o)
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

    return json.dumps(obj, default=helper)


# --- Background Workers ---
async def whisper_worker():
    """Listens to Redis audio stream and processes transcriptions."""
    logger.info("BRIDGE: Whisper background worker started.")

    # Initialize Whisper service
    from handlers.whisper import WhisperService

    service = WhisperService(redis_client)
    await service.initialize()

    async def handler(data: dict):
        try:
            # Data from Redis stream
            # Extract audio and session info
            # The data was serialized as JSON string in publish_event
            audio_hex = data.get("payload", {}).get("audio_data")
            session_id = data.get("payload", {}).get("session_id", "default")

            if audio_hex:
                import numpy as np

                # Convert hex back to bytes
                audio_bytes = bytes.fromhex(audio_hex)
                # Process via Whisper
                await service.process_audio_request(session_id, audio_bytes)

        except Exception as e:
            logger.error(f"BRIDGE: Whisper worker error: {e}")

    await redis_client.listen_stream("audio_stream", "h-bridge-whisper", "whisper-1", handler)


@app.on_event("startup")
async def startup_event():
    await redis_client.connect()
    await voice_profile_service.initialize()
    await voice_modulation_service.initialize()
    await prosody_service.initialize()
    asyncio.create_task(agent_discovery_worker())
    asyncio.create_task(whisper_worker())


# Admin Token Consumption API
from datetime import datetime, timedelta
from typing import Optional, List, Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../h-core/src"))
from features.admin.token_tracking import TokenTrackingService

token_tracking_service = TokenTrackingService(surreal_client)


@app.get("/api/admin/token-usage")
async def get_token_usage(
    agent_id: Optional[str] = None, limit: int = 100, _: TokenPayload = Depends(require_admin())
) -> List[dict[str, Any]]:
    """Get token usage per agent (AC1)"""
    if agent_id:
        agent_id = validate_agent_id(agent_id)
    if agent_id:
        usage = await token_tracking_service.get_agent_usage(agent_id, limit)
    else:
        usage = await token_tracking_service.get_all_usage(limit)
    return [u.to_dict() for u in usage]


@app.get("/api/admin/token-cost-summary")
async def get_token_cost_summary(
    start_date: Optional[str] = None, end_date: Optional[str] = None, _: TokenPayload = Depends(require_admin())
) -> List[dict[str, Any]]:
    """Get cost summary per agent with calculated costs (AC2)"""
    start_time = None
    end_time = None

    if start_date:
        start_time = datetime.fromisoformat(start_date)
    if end_date:
        end_time = datetime.fromisoformat(end_date)

    return await token_tracking_service.get_cost_summary_by_agent(start_time, end_time)


@app.get("/api/admin/token-trends/daily")
async def get_daily_trends(
    days: int = 30, agent_id: Optional[str] = None, _: TokenPayload = Depends(require_admin())
) -> List[dict[str, Any]]:
    """Get daily token consumption trends (AC3)"""
    if agent_id:
        agent_id = validate_agent_id(agent_id)
    return await token_tracking_service.get_daily_trends(days, agent_id)


@app.get("/api/admin/token-trends/weekly")
async def get_weekly_trends(
    weeks: int = 12, agent_id: Optional[str] = None, _: TokenPayload = Depends(require_admin())
) -> List[dict[str, Any]]:
    """Get weekly token consumption trends (AC3)"""
    if agent_id:
        agent_id = validate_agent_id(agent_id)
    return await token_tracking_service.get_weekly_trends(weeks, agent_id)


@app.get("/api/admin/token-trends/monthly")
async def get_monthly_trends(
    months: int = 12, agent_id: Optional[str] = None, _: TokenPayload = Depends(require_admin())
) -> List[dict[str, Any]]:
    """Get monthly token consumption trends (AC3)"""
    if agent_id:
        agent_id = validate_agent_id(agent_id)
    return await token_tracking_service.get_monthly_trends(months, agent_id)


# Admin Agent Management API
from features.admin.agent_management import AgentManagementService

agent_management_service = AgentManagementService(redis_client, discovered_agents)


@app.get("/api/admin/agents")
async def list_all_agents(_: TokenPayload = Depends(require_admin())):
    """List all agents with their status"""
    return await agent_management_service.list_agents()


@app.get("/api/admin/agents/{agent_id}/status")
async def get_agent_status(agent_id: str, _: TokenPayload = Depends(require_admin())):
    """Get status of a specific agent"""
    agent_id = validate_agent_id(agent_id)
    return await agent_management_service.get_agent_status(agent_id)


@app.post("/api/admin/agents/{agent_id}/enable")
async def enable_agent(agent_id: str, _: TokenPayload = Depends(require_admin())):
    """Enable an agent"""
    agent_id = validate_agent_id(agent_id)
    result = await agent_management_service.enable_agent(agent_id)
    if result.get("success"):
        await redis_client.publish_event(
            "system_stream",
            {
                "type": "admin.agent.enable",
                "sender": {"agent_id": "admin", "role": "admin"},
                "recipient": {"target": agent_id},
                "payload": {"content": {"agent_id": agent_id}},
            },
        )
    return result


@app.post("/api/admin/agents/{agent_id}/disable")
async def disable_agent(agent_id: str, _: TokenPayload = Depends(require_admin())):
    """Disable an agent"""
    agent_id = validate_agent_id(agent_id)
    result = await agent_management_service.disable_agent(agent_id)
    if result.get("success"):
        await redis_client.publish_event(
            "system_stream",
            {
                "type": "admin.agent.disable",
                "sender": {"agent_id": "admin", "role": "admin"},
                "recipient": {"target": agent_id},
                "payload": {"content": {"agent_id": agent_id}},
            },
        )
    return result


# Admin Agent Config API
from features.admin.agent_config import AgentConfigService

agent_config_service = AgentConfigService(surreal_client, None)


@app.put("/api/admin/agents/{agent_id}/parameters")
async def update_agent_parameters(
    agent_id: str, parameters: dict[str, Any], _: TokenPayload = Depends(require_admin())
):
    """Configure agent parameters"""
    agent_id = validate_agent_id(agent_id)
    return await agent_config_service.save_config(agent_id, parameters)


@app.get("/api/admin/agents/{agent_id}/parameters")
async def get_agent_parameters(agent_id: str, _: TokenPayload = Depends(require_admin())):
    """Get agent parameters"""
    agent_id = validate_agent_id(agent_id)
    return await agent_config_service.get_config(agent_id)


# Admin Agent Creation API
from features.admin.agent_creation import AgentCreationService

agent_creation_service = AgentCreationService(surreal_client, None, None, None)


@app.post("/api/admin/agents")
async def create_agent(payload: dict[str, Any], _: TokenPayload = Depends(require_admin())):
    """Create a new agent"""
    from src.features.admin.agent_creation.models import AgentCreationPayload

    name = payload.get("name", "")
    if name:
        name = validate_agent_id(name)

    description = payload.get("description", "")
    if "<script>" in str(description).lower() or "javascript:" in str(description).lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid description: potential XSS detected"
        )

    try:
        creation_payload = AgentCreationPayload(
            name=name,
            description=description,
            agent_type=payload.get("type", "assistant"),
            agents_folder=payload.get("agents_folder"),
        )
    except Exception as e:
        return {"success": False, "error": f"Invalid payload: {str(e)}"}

    return await agent_creation_service.create_agent(creation_payload)


# Admin Provider Config API
from features.admin.provider_config import ProviderConfigService

provider_config_service = ProviderConfigService(agent_config_service)

# Visual Config Service
import sys
import os as _os

sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "../../h-core/src"))
from features.admin.visual_config import VisualConfigService

visual_config_service = VisualConfigService()


@app.get("/api/admin/providers")
async def list_providers(_: TokenPayload = Depends(require_admin())):
    """List all supported LLM providers"""
    return await provider_config_service.list_providers()


@app.get("/api/admin/providers/{provider}")
async def get_provider_info(provider: str, _: TokenPayload = Depends(require_admin())):
    """Get provider information"""
    return await provider_config_service.get_provider_info(provider)


@app.put("/api/admin/providers/{provider}")
async def configure_provider(
    provider: str, config: dict[str, Any], agent_id: str = "default", _: TokenPayload = Depends(require_admin())
):
    """Configure LLM provider for an agent"""
    agent_id = validate_agent_id(agent_id)
    return await provider_config_service.configure_provider(
        agent_id=agent_id,
        provider=provider,
        model=config.get("model"),
        base_url=config.get("endpoint"),
        api_key=config.get("apiKey"),
    )


# Visual API Endpoints
@app.get("/api/visual/config")
async def get_visual_config():
    """Get current visual configuration"""
    return await visual_config_service.get_config()


@app.put("/api/visual/config")
async def update_visual_config(config: dict[str, Any], _: TokenPayload = Depends(require_admin())):
    """Update visual configuration"""
    return await visual_config_service.update_config(config)


@app.get("/api/visual/providers")
async def list_visual_providers():
    """List all supported visual providers"""
    from features.admin.visual_config.service import list_visual_providers

    return list_visual_providers()


@app.get("/api/visual/providers/{provider}")
async def get_visual_provider_info(provider: str):
    """Get visual provider information"""
    from features.admin.visual_config.service import get_visual_provider_info

    return get_visual_provider_info(provider)


@app.get("/api/visual/providers/{provider}/capabilities")
async def get_visual_provider_capabilities(provider: str):
    """Get visual provider capabilities"""
    from features.admin.visual_config.service import get_visual_provider_info

    info = get_visual_provider_info(provider)
    return {
        "provider": provider,
        "supports_reference_images": info.get("supports_reference_images", False),
        "supports_style_preset": info.get("supports_style_preset", False),
        "supports_aspect_ratio": info.get("supports_aspect_ratio", False),
        "supports_loras": info.get("supports_loras", False),
    }


@app.get("/api/visual/providers/{provider}/health")
async def get_visual_provider_health(provider: str):
    """Get visual provider health status"""
    from features.admin.visual_config.service import is_valid_provider

    if not is_valid_provider(provider):
        return {"status": "unknown", "provider": provider}
    return {"status": "available", "provider": provider}


@app.post("/api/visual/generate")
async def generate_visual(data: dict[str, Any], _: TokenPayload = Depends(require_admin())):
    """Generate image with specified provider"""
    from features.admin.visual_config.service import is_valid_provider

    provider = data.get("provider")
    prompt = data.get("prompt", "")
    agent_id = data.get("agent_id", "system")
    fallback = data.get("fallback", True)

    config = await visual_config_service.get_config()
    effective_provider = provider or config.get("provider", "nanobanana")

    if provider and not is_valid_provider(provider):
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    return {
        "status": "not_implemented",
        "message": "Visual generation requires h-core service",
        "provider": effective_provider,
        "prompt": prompt,
        "agent_id": agent_id,
    }


@app.put("/api/agents/{agent_id}/visual/provider")
async def set_agent_visual_provider(agent_id: str, data: dict[str, Any], _: TokenPayload = Depends(require_admin())):
    """Set visual provider for a specific agent"""
    agent_id = validate_agent_id(agent_id)
    provider = data.get("provider")
    return await visual_config_service.set_agent_provider(agent_id, provider)


@app.get("/api/agents/{agent_id}/visual/provider")
async def get_agent_visual_provider(agent_id: str, _: TokenPayload = Depends(require_admin())):
    """Get visual provider for a specific agent"""
    agent_id = validate_agent_id(agent_id)
    provider = await visual_config_service.get_agent_provider(agent_id)
    return {"agent_id": agent_id, "provider": provider or (await visual_config_service.get_config()).get("provider")}


@app.post("/api/visual/outfit")
async def generate_outfit(data: dict[str, Any], _: TokenPayload = Depends(require_admin())):
    """Generate outfit image"""
    agent_id = data.get("agent_id", "system")
    outfit_description = data.get("outfit_description", "")
    preset = data.get("preset")
    save_to_vault = data.get("save_to_vault", False)

    prompt = outfit_description
    if preset:
        prompt = f"{preset} outfit"

    return {
        "status": "not_implemented",
        "message": "Outfit generation requires h-core service",
        "agent_id": agent_id,
        "outfit_description": outfit_description,
        "preset": preset,
        "save_to_vault": save_to_vault,
    }


@app.get("/api/visual/outfits/{agent_id}")
async def get_outfit_history(agent_id: str, _: TokenPayload = Depends(require_admin())):
    """Get outfit history for an agent"""
    return {"agent_id": agent_id, "outfits": []}


# =============================================
# Spatial API Endpoints (Epic 9)
# =============================================
from services.spatial import SpatialAPIService

spatial_service = SpatialAPIService(surreal_client)


@app.on_event("startup")
async def init_spatial_service():
    await spatial_service.initialize()


@app.post("/api/spatial/agents/{agent_id}/room")
async def assign_agent_to_room(agent_id: str, data: dict):
    """Assign agent to a room"""
    room = data.get("room")
    if not room:
        return {"success": False, "error": "room is required"}
    return await spatial_service.assign_agent_to_room(agent_id, room)


@app.get("/api/spatial/agents/{agent_id}/room")
async def get_agent_room(agent_id: str):
    """Get agent's current room"""
    room = await spatial_service.get_agent_room(agent_id)
    if room:
        return room
    return {"room_id": None, "message": "Agent not assigned to any room"}


@app.delete("/api/spatial/agents/{agent_id}/room")
async def remove_agent_from_room(agent_id: str):
    """Remove agent from room"""
    return await spatial_service.remove_agent_from_room(agent_id)


@app.get("/api/spatial/rooms")
async def list_rooms():
    """List all available rooms"""
    return await spatial_service.get_rooms()


@app.get("/api/spatial/rooms/{room_id}/agents")
async def get_agents_in_room(room_id: str):
    """List agents in a specific room"""
    return await spatial_service.get_room_agents(room_id)


@app.get("/api/spatial/agents/{agent_id}/location")
async def get_agent_location(agent_id: str):
    """Get agent's current location"""
    location = await spatial_service.get_agent_location(agent_id)
    if location:
        return location
    return {"agent_id": agent_id, "room_id": None, "message": "Location unknown"}


@app.put("/api/spatial/agents/{agent_id}/location")
async def update_agent_location(agent_id: str, data: dict):
    """Update agent's location"""
    room = data.get("room")
    if not room:
        return {"success": False, "error": "room is required"}
    confidence = data.get("confidence")
    return await spatial_service.update_agent_location(agent_id, room, confidence)


@app.get("/api/spatial/agents/{agent_id}/location/history")
async def get_location_history(agent_id: str, limit: int = 10):
    """Get agent's location history"""
    return await spatial_service.get_agent_location_history(agent_id, limit)


@app.post("/api/spatial/mobile/location")
async def receive_mobile_location(data: dict):
    """Receive location from mobile client"""
    return await spatial_service.handle_mobile_location(data)


@app.get("/api/spatial/spaces/exterior")
async def get_exterior_info():
    """Get exterior space information"""
    return await spatial_service.get_exterior_info()


@app.put("/api/spatial/users/{user_id}/space")
async def set_user_space(user_id: str, data: dict):
    """Set user space (interior/exterior)"""
    space = data.get("space")
    if not space:
        return {"success": False, "error": "space is required"}
    return await spatial_service.set_user_space(user_id, space)


@app.get("/api/spatial/themes")
async def list_themes():
    """List all available themes"""
    return await spatial_service.get_themes()


@app.put("/api/spatial/theme")
async def set_theme(data: dict):
    """Set active theme"""
    theme = data.get("theme")
    if not theme:
        return {"success": False, "error": "theme is required"}
    return await spatial_service.set_theme(theme)


@app.get("/api/spatial/agents/{agent_id}/theme")
async def get_agent_theme(agent_id: str):
    """Get agent's current theme"""
    return await spatial_service.get_agent_theme(agent_id)


# =============================================
# Social Arbiter API Endpoints (Epic 3)
# =============================================
from services.arbiter import ArbiterAPIService

arbiter_service = ArbiterAPIService(redis_client, surreal_client)


@app.on_event("startup")
async def init_arbiter_service():
    await arbiter_service.initialize()


@app.post("/api/arbiter/select")
async def select_agent(data: dict):
    """
    Select best agent for a message.

    Request body:
        - message: The user's message
        - context: Optional context (emotional_context, mentioned_agents, sender_id)
    """
    message = data.get("message", "")
    context = data.get("context", {})

    if not message:
        return {"success": False, "error": "message is required"}

    result = await arbiter_service.select_agent(message, context)
    return result


@app.post("/api/arbiter/score")
async def score_agents(data: dict):
    """
    Get agent scores for a message.

    Request body:
        - message: The user's message
        - agents: Optional list of agent IDs to score (if empty, scores all agents)
    """
    message = data.get("message", "")
    agents = data.get("agents", [])

    if not message:
        return {"success": False, "error": "message is required"}

    result = await arbiter_service.score_agents(message, agents if agents else None)
    return result


@app.get("/api/arbiter/config")
async def get_arbiter_config():
    """Get arbiter configuration including registered agents and settings."""
    return arbiter_service.get_config()


@app.get("/api/arbiter/topics")
async def extract_topics(message: str):
    """Extract topics/keywords from a message."""
    if not message:
        return {"success": False, "error": "message parameter is required"}
    return arbiter_service.get_topics(message)


@app.get("/api/arbiter/emotions")
async def detect_emotions(message: str):
    """Detect emotions in a message."""
    if not message:
        return {"success": False, "error": "message parameter is required"}
    return arbiter_service.get_emotions(message)


@app.get("/api/arbiter/suppression/stats")
async def get_suppression_stats():
    """Get suppression statistics."""
    return arbiter_service.get_suppression_stats()


@app.get("/api/arbiter/debug")
async def debug_arbiter_scoring(message: str):
    """Debug endpoint - returns scores for all agents."""
    result = await arbiter_service.debug_scoring(message)
    return result


@app.post("/api/arbiter/agents")
async def add_arbiter_agent(manifest: dict):
    """Register a new agent with the arbiter."""
    agent_id = manifest.get("id")
    if not agent_id:
        return {"success": False, "error": "id is required"}
    return await arbiter_service.add_agent_from_manifest(manifest)


# =============================================
# Memory Isolation API Endpoints (Epic 6)
# =============================================
from services.memory_isolation import MemoryIsolationService

memory_isolation_service = MemoryIsolationService(redis_client, surreal_client)


@app.on_event("startup")
async def init_memory_isolation_service():
    await memory_isolation_service.initialize()


@app.post("/api/users")
async def create_user(data: dict):
    """
    Create a new user.

    Request body:
        - id: User ID
        - email: User email
        - name: User name
    """
    user_id = data.get("id")
    email = data.get("email", "")
    name = data.get("name", "")

    if not user_id:
        return {"success": False, "error": "user id is required"}

    return await memory_isolation_service.create_user(user_id, email, name)


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user and all their session memories."""
    success = await memory_isolation_service.delete_user(user_id)
    return {"success": success}


@app.post("/api/memory/store")
async def store_memory(data: dict):
    """
    Store memory for a specific user and session.

    Request body:
        - userId: User ID
        - sessionId: Session ID
        - data: Memory data (optional)
        - memory: Memory string (optional)
        - emotionalContext: Emotional context dict (optional)
        - context: Context dict (optional)
        - Any other fields will be stored as extra data
    """
    user_id = data.get("userId")
    session_id = data.get("sessionId")

    # Extract any extra fields
    extra_fields = {
        k: v
        for k, v in data.items()
        if k not in ("userId", "sessionId", "data", "memory", "emotionalContext", "context")
    }

    return await memory_isolation_service.store_memory(
        user_id=user_id,
        session_id=session_id,
        data=data.get("data"),
        memory=data.get("memory"),
        emotional_context=data.get("emotionalContext"),
        context=data.get("context"),
        extra_data=extra_fields,
    )


@app.get("/api/memory/{user_id}")
async def get_user_memory(user_id: str, sessionId: Optional[str] = None):
    """
    Get memory for a specific user (with session validation).

    Query params:
        - sessionId: Session ID (optional, auto-generated if not provided)
    """
    result = await memory_isolation_service.get_memory(user_id, sessionId)

    if "error" in result:
        status_code = result.get("status", 403)
        raise HTTPException(status_code=status_code, detail=result.get("message"))

    return result


@app.get("/api/memory/{user_id}/emotional")
async def get_emotional_context(user_id: str, sessionId: Optional[str] = None):
    """
    Get emotional context for a specific user (with session validation).

    Query params:
        - sessionId: Session ID (required)
    """
    if not sessionId:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="sessionId is required")

    result = await memory_isolation_service.get_emotional_context(user_id, sessionId)

    if "error" in result:
        status_code = result.get("status", 403)
        raise HTTPException(status_code=status_code, detail=result.get("message"))

    return result


@app.get("/api/memory/{user_id}/context")
async def get_context(user_id: str, sessionId: Optional[str] = None):
    """
    Get context for a specific user (with session validation).

    Query params:
        - sessionId: Session ID (required)
    """
    if not sessionId:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="sessionId is required")

    result = await memory_isolation_service.get_context(user_id, sessionId)

    if "error" in result:
        status_code = result.get("status", 403)
        raise HTTPException(status_code=status_code, detail=result.get("message"))

    return result


@app.get("/api/memory/list/{user_id}")
async def list_memories(user_id: str, sessionId: Optional[str] = None):
    """
    List all memories for a user (with session validation).

    Query params:
        - sessionId: Session ID (required)
    """
    if not sessionId:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="sessionId is required")

    result = await memory_isolation_service.list_memories(user_id, sessionId)

    if "error" in result:
        status_code = result.get("status", 403)
        raise HTTPException(status_code=status_code, detail=result.get("message"))

    return result


# =============================================
# Internal Memory API Endpoints (Epic 13)
# =============================================


@app.post("/internal/memory/sleep-cycle")
async def trigger_sleep_cycle(
    decay_rate: Optional[float] = None,
    threshold: Optional[float] = 0.1,
    run_decay: bool = True,
    run_cleanup: bool = True,
):
    """
    Trigger the sleep cycle for memory decay and cleanup.

    This endpoint is designed to be called internally or via CLI for periodic maintenance.

    Query params:
        - decay_rate: Decay rate (e.g., 0.05 for 5% decay). Default: 0.1
        - threshold: Strength threshold below which memories are deleted. Default: 0.1
        - run_decay: Whether to run decay. Default: True
        - run_cleanup: Whether to clean orphaned facts. Default: True

    Returns:
        JSON with results of each phase
    """
    from infrastructure.surrealdb import SurrealDbClient

    results = {
        "decay": {"memories_removed": 0, "status": "skipped"},
        "cleanup": {"orphans_removed": 0, "status": "skipped"},
    }

    try:
        # Initialize SurrealDB client
        surreal = SurrealDbClient(surreal_url, os.getenv("SURREAL_USER", "root"), os.getenv("SURREAL_PASS", "root"))
        await surreal.connect()

        # Run decay if requested
        if run_decay:
            removed = await surreal.apply_decay_to_all_memories(decay_rate=decay_rate or 0.1, threshold=threshold)
            results["decay"] = {"memories_removed": removed, "status": "completed"}

        # Run cleanup if requested
        if run_cleanup:
            orphans = await surreal.cleanup_orphaned_facts()
            results["cleanup"] = {"orphans_removed": orphans, "status": "completed"}

        await surreal.close()

        return {"status": "success", "message": "Sleep cycle completed", "results": results}

    except Exception as e:
        logger.error(f"Sleep cycle failed: {e}")
        return {"status": "error", "message": str(e), "results": results}


# =============================================
# Voice API Endpoints (Epic 5)
# =============================================


@app.get("/api/voice/config")
async def get_voice_config():
    """Get voice configuration"""
    return {
        "status": "ok",
        "default_voice": "default",
        "available_voices": voice_profile_service.list_profiles(),
        "available_emotions": voice_modulation_service.get_available_emotions(),
        "available_prosody_styles": prosody_service.get_available_styles(),
    }


@app.post("/api/voice/test")
async def test_voice(data: dict):
    """Test voice synthesis with given parameters"""
    text = data.get("text", "Hello world")
    agent_id = data.get("agent_id", "default")
    emotion = data.get("emotion", "neutral")
    prosody_style = data.get("prosody_style", "default")

    base_params = voice_profile_service.apply_to_tts_params(agent_id, {"pitch": 1.0, "rate": 1.0, "volume": 1.0})

    if emotion:
        base_params = voice_modulation_service.modulate_voice(base_params, emotion)

    base_params = prosody_service.apply_prosody(base_params, text, style=prosody_style)

    return {
        "status": "ok",
        "text": text,
        "agent_id": agent_id,
        "voice_params": {
            "pitch": base_params.get("pitch"),
            "rate": base_params.get("rate"),
            "volume": base_params.get("volume"),
            "emotion": emotion,
            "prosody_style": prosody_style,
        },
    }


@app.get("/api/agents/{agent_id}/voice")
async def get_agent_voice(agent_id: str):
    """Get voice profile for an agent"""
    agent_id = validate_agent_id(agent_id)
    profile = voice_profile_service.get_profile(agent_id)
    return profile.to_dict()


@app.put("/api/agents/{agent_id}/voice")
async def set_agent_voice(agent_id: str, data: dict):
    """Set voice profile for an agent"""
    agent_id = validate_agent_id(agent_id)
    profile = voice_profile_service.get_profile(agent_id)
    profile_data = profile.to_dict()
    profile_data.update({k: v for k, v in data.items() if v is not None})
    new_profile = voice_profile_service.VoiceProfile.from_dict(profile_data)
    result = await voice_profile_service.set_profile(agent_id, new_profile)
    return result.to_dict()


@app.get("/api/agents/{agent_id}/voice-modulation")
async def get_agent_voice_modulation(agent_id: str):
    """Get voice modulation settings for an agent"""
    agent_id = validate_agent_id(agent_id)
    settings = await voice_modulation_service.get_agent_modulation_settings(agent_id)
    return {
        "agent_id": agent_id,
        "settings": settings,
        "available_emotions": voice_modulation_service.get_available_emotions(),
    }


@app.put("/api/agents/{agent_id}/voice-modulation")
async def set_agent_voice_modulation(agent_id: str, data: dict):
    """Set voice modulation settings for an agent"""
    agent_id = validate_agent_id(agent_id)
    settings = {"default_emotion": data.get("default_emotion", "neutral"), "intensity": data.get("intensity", 1.0)}
    return await voice_modulation_service.set_agent_modulation_settings(agent_id, settings)


@app.get("/api/agents/{agent_id}/voice/prosody")
async def get_agent_prosody(agent_id: str):
    """Get prosody settings for an agent"""
    agent_id = validate_agent_id(agent_id)
    settings = await prosody_service.get_agent_prosody_settings(agent_id)
    return {"agent_id": agent_id, "settings": settings, "available_styles": prosody_service.get_available_styles()}


@app.put("/api/agents/{agent_id}/voice/prosody")
async def set_agent_prosody(agent_id: str, data: dict):
    """Set prosody settings for an agent"""
    agent_id = validate_agent_id(agent_id)
    settings = {
        "style": data.get("style", "default"),
        "default_intonation": data.get("default_intonation", "statement"),
    }
    return await prosody_service.set_agent_prosody_settings(agent_id, settings)


@app.get("/api/voice/emotions")
async def list_voice_emotions():
    """List all available voice emotions and their configurations"""
    emotions = {}
    for emotion, config in EMOTION_CONFIGS.items():
        emotions[emotion] = {
            "pitch_modifier": config.pitch_modifier,
            "rate_modifier": config.rate_modifier,
            "volume_modifier": config.volume_modifier,
            "description": config.description,
        }
    return emotions


@app.post("/api/voice/detect-emotion")
async def detect_text_emotion(data: dict):
    """Detect emotion from text"""
    text = data.get("text", "")
    if not text:
        return {"error": "text is required"}
    emotion = voice_modulation_service.detect_emotion_from_text(text)
    return {"text": text, "detected_emotion": emotion}


@app.post("/api/voice/analyze-prosody")
async def analyze_text_prosody(data: dict):
    """Analyze prosody in text"""
    text = data.get("text", "")
    if not text:
        return {"error": "text is required"}
    return prosody_service.analyze_text_prosody(text)


# =============================================
# Skills & Plugins API Endpoints (Epic 11)
# =============================================

# In-memory skill/agent registry (integrates with PluginLoader)
skills_enabled: set[str] = set()  # All loaded skills are enabled by default


@app.get("/api/skills")
async def list_skills():
    """
    List all available skills/agents.
    """
    # This would integrate with the PluginLoader's AgentRegistry
    return {
        "skills": [
            # Would be populated from PluginLoader
        ],
        "count": 0,
    }


@app.get("/api/skills/{skill_id}")
async def get_skill(skill_id: str):
    """Get details of a specific skill."""
    return {"skill_id": skill_id, "enabled": skill_id not in skills_enabled, "status": "active"}


@app.post("/api/skills/{skill_id}/enable")
async def enable_skill(skill_id: str):
    """Enable a skill/agent."""
    if skill_id in skills_enabled:
        skills_enabled.discard(skill_id)

    return {"status": "ok", "skill_id": skill_id, "enabled": True}


@app.post("/api/skills/{skill_id}/disable")
async def disable_skill(skill_id: str):
    """Disable a skill/agent."""
    skills_enabled.add(skill_id)

    return {"status": "ok", "skill_id": skill_id, "enabled": False}


@app.get("/api/skills/{skill_id}/status")
async def get_skill_status(skill_id: str):
    """Get the status of a skill."""
    enabled = skill_id not in skills_enabled

    return {"skill_id": skill_id, "enabled": enabled, "status": "active" if enabled else "disabled"}


# =============================================
# Event Subscription API Endpoints (Epic 10 - Story 10-1)
# =============================================

# In-memory store for subscriptions (in production, use Redis or database)
subscriptions: dict[str, list[str]] = {}

# Hardware Events Store (simulated - to integrate with Home Assistant)
hardware_events: list[dict] = []


@app.get("/api/hardware/events")
async def list_hardware_events(
    limit: int = 50,
    event_type: str = None,
):
    """
    List recent hardware events.

    Query params:
        - limit: Maximum number of events to return
        - event_type: Filter by event type (motion, temperature, door, etc.)
    """
    events = hardware_events[-limit:]

    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]

    return {"events": events, "count": len(events)}


@app.post("/api/hardware/events")
async def receive_hardware_event(data: dict):
    """
    Receive a hardware event (from Home Assistant or other sensors).

    Body:
        - event_type: Type of event (motion, temperature, door, light, etc.)
        - device_id: ID of the device/sensor
        - value: Event value/state
        - timestamp: Event timestamp
    """
    event_type = data.get("event_type")
    device_id = data.get("device_id")
    value = data.get("value")
    timestamp = data.get("timestamp")

    if not event_type or not device_id:
        return {"error": "event_type and device_id are required"}, 400

    event = {
        "id": str(uuid4()),
        "event_type": event_type,
        "device_id": device_id,
        "value": value,
        "timestamp": timestamp,
    }

    hardware_events.append(event)

    # Keep only last 1000 events
    if len(hardware_events) > 1000:
        hardware_events[:] = hardware_events[-1000:]

    # Publish to Redis for agents to subscribe
    if redis_client and redis_client.client:
        await redis_client.publish_event("events:hardware", event)

    return {"status": "ok", "event": event}


@app.get("/api/hardware/devices")
async def list_hardware_devices():
    """List all known hardware devices."""
    devices = {}
    for event in hardware_events:
        device_id = event.get("device_id")
        if device_id and device_id not in devices:
            devices[device_id] = {
                "device_id": device_id,
                "event_type": event.get("event_type"),
                "last_value": event.get("value"),
                "last_seen": event.get("timestamp"),
            }

    return {"devices": list(devices.values())}


@app.get("/api/hardware/events/{device_id}")
async def get_device_events(device_id: str, limit: int = 20):
    """Get events for a specific device."""
    device_events = [e for e in hardware_events if e.get("device_id") == device_id]
    device_events = device_events[-limit:]

    return {"device_id": device_id, "events": device_events}


# =============================================
# Calendar API Endpoints (Epic 10 - Story 10-3)
# =============================================

# Calendar events store (simulated - to integrate with Google Calendar, CalDAV)
calendar_events: list[dict] = []


@app.get("/api/calendar/events")
async def list_calendar_events(
    start_date: str = None,
    end_date: str = None,
    limit: int = 50,
):
    """
    List calendar events.

    Query params:
        - start_date: Start date (ISO format)
        - end_date: End date (ISO format)
        - limit: Maximum number of events
    """
    events = calendar_events[-limit:]

    return {"events": events, "count": len(events)}


@app.post("/api/calendar/events")
async def create_calendar_event(data: dict):
    """
    Create a calendar event.

    Body:
        - title: Event title
        - description: Event description
        - start_time: Start time (ISO format)
        - end_time: End time (ISO format)
        - attendees: List of attendee IDs
    """
    title = data.get("title")
    start_time = data.get("start_time")

    if not title or not start_time:
        return {"error": "title and start_time are required"}, 400

    event = {
        "id": str(uuid4()),
        "title": title,
        "description": data.get("description", ""),
        "start_time": start_time,
        "end_time": data.get("end_time"),
        "attendees": data.get("attendees", []),
    }

    calendar_events.append(event)

    return {"status": "ok", "event": event}


@app.get("/api/calendar/events/upcoming")
async def get_upcoming_events(limit: int = 10):
    """Get upcoming events."""
    # Sort by start time and get upcoming
    sorted_events = sorted(calendar_events, key=lambda e: e.get("start_time", ""))
    upcoming = sorted_events[-limit:]

    return {"events": upcoming, "count": len(upcoming)}


# =============================================
# System Stimulus/Entropy API (Epic 10 - Story 10-4)
# =============================================

# Stimulus configuration and history
stimulus_config = {
    "enabled": True,
    "interval_seconds": 3600,  # Every hour
    "max_stimuli_per_day": 10,
}
stimulus_history: list[dict] = []


@app.get("/api/stimulus/config")
async def get_stimulus_config():
    """Get stimulus/entropy configuration."""
    return stimulus_config


@app.post("/api/stimulus/config")
async def update_stimulus_config(data: dict):
    """Update stimulus/entropy configuration."""
    if "enabled" in data:
        stimulus_config["enabled"] = data["enabled"]
    if "interval_seconds" in data:
        stimulus_config["interval_seconds"] = data["interval_seconds"]
    if "max_stimuli_per_day" in data:
        stimulus_config["max_stimuli_per_day"] = data["max_stimuli_per_day"]

    return {"status": "ok", "config": stimulus_config}


@app.post("/api/stimulus/trigger")
async def trigger_stimulus(data: dict = None):
    """
    Manually trigger a system stimulus.

    Body (optional):
        - type: Type of stimulus (entropy, proactive, reminder)
        - context: Additional context for the stimulus
    """
    if not stimulus_config["enabled"]:
        return {"error": "Stimulus is disabled"}, 400

    stimulus_type = data.get("type", "manual") if data else "manual"
    context = data.get("context", {}) if data else {}

    stimulus = {
        "id": str(uuid4()),
        "type": stimulus_type,
        "context": context,
        "triggered_at": str(datetime.now()),
    }

    stimulus_history.append(stimulus)

    # Keep only last 1000 stimuli
    if len(stimulus_history) > 1000:
        stimulus_history[:] = stimulus_history[-1000:]

    # Publish to Redis for agents to react
    if redis_client and redis_client.client:
        await redis_client.publish_event("events:stimulus", stimulus)

    return {"status": "ok", "stimulus": stimulus}


@app.get("/api/stimulus/history")
async def get_stimulus_history(limit: int = 50):
    """Get stimulus history."""
    return {"stimuli": stimulus_history[-limit:], "count": len(stimulus_history[-limit:])}


@app.post("/api/events/subscribe")
async def subscribe_to_event(data: dict):
    """
    Subscribe an agent to an event stream.

    Body:
        - agent_id: Agent identifier
        - event_type: Type of event (system_status, agent_state, user_activity)
    """
    agent_id = data.get("agent_id")
    event_type = data.get("event_type", "system_stream")

    if not agent_id:
        return {"error": "agent_id is required"}, 400

    # Subscribe to the Redis channel
    channel = f"events:{event_type}"

    # Store subscription
    if agent_id not in subscriptions:
        subscriptions[agent_id] = []
    if channel not in subscriptions[agent_id]:
        subscriptions[agent_id].append(channel)

    return {
        "status": "ok",
        "agent_id": agent_id,
        "subscribed_to": channel,
        "subscriptions": subscriptions.get(agent_id, []),
    }


@app.post("/api/events/unsubscribe")
async def unsubscribe_from_event(data: dict):
    """
    Unsubscribe an agent from an event stream.

    Body:
        - agent_id: Agent identifier
        - event_type: Type of event to unsubscribe from
    """
    agent_id = data.get("agent_id")
    event_type = data.get("event_type", "system_stream")

    if not agent_id:
        return {"error": "agent_id is required"}, 400

    channel = f"events:{event_type}"

    # Remove subscription
    if agent_id in subscriptions and channel in subscriptions[agent_id]:
        subscriptions[agent_id].remove(channel)

    return {
        "status": "ok",
        "agent_id": agent_id,
        "unsubscribed_from": channel,
        "subscriptions": subscriptions.get(agent_id, []),
    }


@app.get("/api/events/subscriptions")
async def list_subscriptions(agent_id: str):
    """Get all subscriptions for an agent."""
    if not agent_id:
        return {"error": "agent_id query parameter is required"}, 400

    return {"agent_id": agent_id, "subscriptions": subscriptions.get(agent_id, [])}


@app.get("/api/events/types")
async def list_event_types():
    """List all available event types."""
    return {
        "event_types": [
            {"name": "system_status", "description": "System status changes"},
            {"name": "agent_state", "description": "Agent state changes"},
            {"name": "user_activity", "description": "User activity events"},
            {"name": "system_stream", "description": "General system events"},
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
