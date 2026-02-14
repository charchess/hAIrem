import asyncio
import json
import logging
import os
from uuid import UUID, uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from infrastructure.redis import RedisClient
from infrastructure.surrealdb import SurrealDbClient
from models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender
from handlers.audio import handle_audio_message
from handlers.wakeword import handle_wakeword_message
from handlers.whisper import handle_whisper_request
from handlers.tts import handle_tts_request

# Logging setup
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s:%(name)s:%(message)s')
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
    url=surreal_url,
    user=os.getenv("SURREALDB_USER", "root"),
    password=os.getenv("SURREALDB_PASS", "root")
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
            if isinstance(sender, str): sender = json.loads(sender)
            if isinstance(payload, str): payload = json.loads(payload)

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
                        "total_tokens": status_data.get("total_tokens", 0)
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
                await surreal_client._call('query', 
                    f"INSERT INTO subject (id, name) VALUES ({sid}, $name) ON DUPLICATE KEY UPDATE name = $name;", 
                    {"name": name}
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
        res = await surreal_client._call('query', "SELECT * FROM fact ORDER BY created_at DESC LIMIT 50;")
        messages = res[0].get("result", []) if isinstance(res[0], dict) else res
        return {"messages": messages, "status": "ok"}
    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}")
        return {"messages": [], "status": "error"}

@app.get("/api/debug/error")
async def trigger_debug_error():
    """Simulates a critical system error for UI testing."""
    msg = HLinkMessage(
        type=MessageType.SYSTEM_LOG,
        sender=Sender(agent_id="system", role="orchestrator"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="[ERROR] CRITICAL_SYSTEM_FAILURE: Debug error triggered via API")
    )
    await redis_client.publish_event("system_stream", msg.model_dump())
    return {"status": "debug_error_sent"}

# --- WebSocket Bridge ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("New A2UI client connected.")
    
    # STORY 14.1 FIX: Send immediate confirmation to UI to unlock input
    await websocket.send_text(json.dumps({
        "type": "system.status_update",
        "sender": {"agent_id": "bridge", "role": "gateway"},
        "recipient": {"target": "user"},
        "payload": {"content": {"component": "ws", "status": "ok"}}
    }))
    
    # Also send a welcome log
    await websocket.send_text(json.dumps({
        "type": "system.log",
        "payload": {"content": "BRIDGE: Connexion établie. Système prêt."}
    }))
    
    async def redis_to_ws():
        if not redis_client.client:
            await redis_client.connect()
        
        async def handler(data: dict):
            try:
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
                    await websocket.send_text(json.dumps({
                        "type": "system.log",
                        "payload": {"content": str(content)}
                    }))
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
                msg_type = raw_msg.get('type')
                
                # Route to appropriate handler based on message type
                if msg_type in ['user_audio', 'audio_session_request', 'audio_session_stop', 'audio_session_status']:
                    await handle_audio_message(websocket, raw_msg, redis_client)
                elif msg_type in ['wakeword_status_request', 'wakeword_enable', 'wakeword_disable']:
                    await handle_wakeword_message(websocket, raw_msg, redis_client)
                elif msg_type in ['whisper_session_start', 'whisper_session_end', 'whisper_audio_data', 'whisper_status']:
                    await handle_whisper_request(websocket, raw_msg, redis_client)
                elif msg_type == 'tts_request':
                    await handle_tts_request(websocket, raw_msg, redis_client)
                else:
                    # Default HLink message handling for other types
                    if all(k in raw_msg for k in ["type", "sender", "recipient", "payload"]):
                        msg, error = HLinkMessage.validate_message(raw_msg)
                        if not error:
                            # STORY 14.1 FIX: Use mode='json' to ensure UUID/datetime are serialized
                            await redis_client.publish_event("system_stream", msg.model_dump(mode='json'))
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
            audio_hex = data.get('payload', {}).get('audio_data')
            session_id = data.get('payload', {}).get('session_id', 'default')
            
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
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[dict[str, Any]]:
    """Get token usage per agent (AC1)"""
    if agent_id:
        usage = await token_tracking_service.get_agent_usage(agent_id, limit)
    else:
        usage = await token_tracking_service.get_all_usage(limit)
    return [u.to_dict() for u in usage]

@app.get("/api/admin/token-cost-summary")
async def get_token_cost_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
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
    days: int = 30,
    agent_id: Optional[str] = None
) -> List[dict[str, Any]]:
    """Get daily token consumption trends (AC3)"""
    return await token_tracking_service.get_daily_trends(days, agent_id)

@app.get("/api/admin/token-trends/weekly")
async def get_weekly_trends(
    weeks: int = 12,
    agent_id: Optional[str] = None
) -> List[dict[str, Any]]:
    """Get weekly token consumption trends (AC3)"""
    return await token_tracking_service.get_weekly_trends(weeks, agent_id)

@app.get("/api/admin/token-trends/monthly")
async def get_monthly_trends(
    months: int = 12,
    agent_id: Optional[str] = None
) -> List[dict[str, Any]]:
    """Get monthly token consumption trends (AC3)"""
    return await token_tracking_service.get_monthly_trends(months, agent_id)

# Admin Agent Management API
from features.admin.agent_management import AgentManagementService

agent_management_service = AgentManagementService(redis_client, discovered_agents)

@app.get("/api/admin/agents")
async def list_all_agents():
    """List all agents with their status"""
    return await agent_management_service.list_agents()

@app.get("/api/admin/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get status of a specific agent"""
    return await agent_management_service.get_agent_status(agent_id)

@app.post("/api/admin/agents/{agent_id}/enable")
async def enable_agent(agent_id: str):
    """Enable an agent"""
    result = await agent_management_service.enable_agent(agent_id)
    if result.get("success"):
        await redis_client.publish_event("system_stream", {
            "type": "admin.agent.enable",
            "sender": {"agent_id": "admin", "role": "admin"},
            "recipient": {"target": agent_id},
            "payload": {"content": {"agent_id": agent_id}}
        })
    return result

@app.post("/api/admin/agents/{agent_id}/disable")
async def disable_agent(agent_id: str):
    """Disable an agent"""
    result = await agent_management_service.disable_agent(agent_id)
    if result.get("success"):
        await redis_client.publish_event("system_stream", {
            "type": "admin.agent.disable",
            "sender": {"agent_id": "admin", "role": "admin"},
            "recipient": {"target": agent_id},
            "payload": {"content": {"agent_id": agent_id}}
        })
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)