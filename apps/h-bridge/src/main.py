import asyncio
import json
import logging
import os
from uuid import UUID, uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender

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
public_path = "/app/static"
redis_host = os.getenv("REDIS_HOST", "redis")
surreal_url = os.getenv("SURREALDB_URL", "ws://surrealdb:8000/rpc")

# Infrastructure Clients
redis_client = RedisClient(host=redis_host)
surreal_client = SurrealDbClient(
    url=surreal_url,
    user=os.getenv("SURREALDB_USER", "root"),
    password=os.getenv("SURREALDB_PASS", "root")
)

# Global agent cache for the API
discovered_agents = {}

async def agent_discovery_worker():
    """Listens for agent status updates to populate discovered_agents."""
    logger.info("BRIDGE: Discovery worker started.")
    
    async def handler(msg: HLinkMessage):
        if msg.type == MessageType.SYSTEM_STATUS_UPDATE:
            agent_id = msg.sender.agent_id
            # Ignore core/system status for the agent list
            if agent_id in ["core", "system"]:
                return
                
            status_data = msg.payload.content
            if isinstance(status_data, dict):
                discovered_agents[agent_id] = {
                    "id": agent_id,
                    "active": status_data.get("active", True),
                    "personified": status_data.get("personified", True),
                    "commands": status_data.get("commands", []),
                    "prompt_tokens": status_data.get("prompt_tokens", 0),
                    "completion_tokens": status_data.get("completion_tokens", 0),
                    "total_tokens": status_data.get("total_tokens", 0)
                }

    await redis_client.subscribe("broadcast", handler)

# --- API Endpoints ---
@app.get("/api/agents")
async def get_agents():
    """Returns the list of agents discovered via Redis status updates."""
    return list(discovered_agents.values())

@app.get("/api/history")
async def get_history():
    if not surreal_client.client:
        return {"messages": [], "status": "connecting"}
    try:
        messages = await surreal_client.get_messages(limit=50)
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
    await redis_client.publish("broadcast", msg)
    return {"status": "debug_error_sent"}

# --- WebSocket Bridge ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("New A2UI client connected.")
    
    # STORY 14.1: Audio Ingestion Buffer
    audio_queue = asyncio.Queue()
    
    async def redis_to_ws():
        if not redis_client.client:
            await redis_client.connect()
        
        async def handler(msg: HLinkMessage):
            await websocket.send_text(msg.model_dump_json())

        await redis_client.subscribe("broadcast", handler)

    try:
        # Run redis listener in background
        listen_task = asyncio.create_task(redis_to_ws())
        
        while True:
            # Receive from UI
            data = await websocket.receive_text()
            try:
                raw_msg = json.loads(data)
                
                # Check for binary audio data (Story 14.1)
                if raw_msg.get("type") == "audio_blob":
                    # Handle binary audio ingestion
                    pass
                
                msg = HLinkMessage(**raw_msg)
                
                # Persistence (Optional: Bridge only relays, Core persists)
                # await surreal_client.save_message(msg)
                
                # Dispatch to Redis
                target_channel = "broadcast" if msg.recipient.target == "broadcast" else f"agent:{msg.recipient.target}"
                await redis_client.publish(target_channel, msg)
                
            except Exception as e:
                logger.error(f"Error processing WS message: {e}")
                
    except WebSocketDisconnect:
        logger.info("A2UI client disconnected.")
        listen_task.cancel()
    except Exception as e:
        logger.error(f"WS Bridge Error: {e}")

@app.on_event("startup")
async def startup_event():
    await redis_client.connect()
    asyncio.create_task(agent_discovery_worker())

@app.get("/")
async def root():
    return {"status": "hAIrem Bridge Active"}