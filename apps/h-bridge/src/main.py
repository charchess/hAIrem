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
                # logger.debug(f"BRIDGE: Discovered/Updated agent {agent_id}")

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
    
    async def redis_to_ws():
        if not redis_client.client:
            await redis_client.connect()
        pubsub = redis_client.client.pubsub()
        await pubsub.subscribe("broadcast", "agent:user")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await websocket.send_json(data)
                    except Exception as e:
                        logger.error(f"WS Send Error: {e}")
        except asyncio.CancelledError:
            logger.info("Redis-to-WS bridge task cancelled.")
        finally:
            await pubsub.unsubscribe()

    # Launch background task
    rtw_task = asyncio.create_task(redis_to_ws())
    
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except Exception as e:
                logger.error(f"WS_RECEIVE_ERROR: {e}")
                break
                
            msg_type = data.get("type")
            
            # Robust UUID handling
            msg_id_str = data.get("id")
            try:
                msg_id = UUID(msg_id_str) if msg_id_str else uuid4()
            except (ValueError, TypeError):
                msg_id = uuid4()
            
            sender = Sender(agent_id="user", role="user")
            
            if msg_type == "narrative.text":
                payload = data.get("payload", {})
                content = payload.get("content") if isinstance(payload, dict) else data.get("content")
                recipient = data.get("recipient", {})
                target = recipient.get("target") if isinstance(recipient, dict) else data.get("target", "Renarde")
                
                if target and str(target).lower() != "broadcast":
                    target = str(target).capitalize()
                else:
                    target = str(target) if target else "Renarde"

                hlink_msg = HLinkMessage(
                    id=msg_id,
                    type=MessageType.NARRATIVE_TEXT,
                    sender=sender,
                    recipient=Recipient(target=target),
                    payload=Payload(content=content)
                )
                await redis_client.publish(f"agent:{target}", hlink_msg)
                # STORY 23.2: Also publish to broadcast for global persistence/observability
                await redis_client.publish("broadcast", hlink_msg)
            
            elif msg_type == "expert.command":
                payload = data.get("payload", {})
                content_dict = payload.get("content", {}) if isinstance(payload.get("content"), dict) else {}
                command = content_dict.get("command") or payload.get("command") or data.get("command")
                args = content_dict.get("args") or payload.get("args") or data.get("args") or ""
                recipient = data.get("recipient", {})
                target = recipient.get("target") if isinstance(recipient, dict) else data.get("agent_id", "Renarde")
                
                target_str = str(target) if target else "Renarde"

                hlink_msg = HLinkMessage(
                    id=msg_id,
                    type=MessageType.EXPERT_COMMAND,
                    sender=sender,
                    recipient=Recipient(target=target_str),
                    payload=Payload(
                        content=None,
                        # Note: command and args are usually part of the content for expert commands, 
                        # but Payload schema is simple (content, format, emotion).
                        # We might need to pack them into content or extending Payload if needed.
                        # For now, sticking to the schema by putting them in content if it's a dict, 
                        # or passing the specific dictionary expected by the consumer.
                        # Wait, the previous code had payload={"content": None, "command": ..., "args": ...}
                        # This implies the Pydantic model Payload might be too restrictive or we were bypassing it.
                        # Let's check Payload definition again: class Payload(BaseModel): content: Any ...
                        # So we can put the dict in 'content'.
                    )
                )
                # Correction: The previous code was bypassing the Payload model and passing a dict to the HLinkMessage payload field directly.
                # Since HLinkMessage expects 'payload: Payload', we must wrap it.
                # However, the previous code structure: payload={"content": None, "command": ..., "args": ...}
                # does NOT match Payload(content=Any, format=..., emotion=...).
                # It looks like the 'expert.command' logic was relying on a loose dict structure.
                # To be type safe and logic safe, we should probably put the command/args INSIDE the 'content' field of the Payload.
                
                hlink_msg = HLinkMessage(
                    id=msg_id,
                    type=MessageType.EXPERT_COMMAND,
                    sender=sender,
                    recipient=Recipient(target=target_str),
                    payload=Payload(content={
                        "command": command,
                        "args": args
                    })
                )
                await redis_client.publish(f"agent:{target_str}", hlink_msg)
                # STORY 23.2: Also publish to broadcast for global persistence
                await redis_client.publish("broadcast", hlink_msg)

            elif msg_type == "system.status_update":
                payload = data.get("payload", {})
                content = payload.get("content") if isinstance(payload, dict) else payload
                hlink_msg = HLinkMessage(
                    id=msg_id,
                    type=MessageType.SYSTEM_STATUS_UPDATE,
                    sender=sender,
                    recipient=Recipient(target="broadcast"),
                    payload=Payload(content=content)
                )
                await redis_client.publish("agent:broadcast", hlink_msg)

            elif msg_type == "system.config_update":
                # Config updates are sent to broadcast for Core to pick up
                payload_content = data.get("content") or data
                hlink_msg = HLinkMessage(
                    type=MessageType.SYSTEM_CONFIG_UPDATE,
                    sender=sender,
                    recipient=Recipient(target="broadcast"),
                    payload=Payload(content=payload_content)
                )
                await redis_client.publish("broadcast", hlink_msg)

    except WebSocketDisconnect:
        logger.info("A2UI client disconnected.")
    finally:
        rtw_task.cancel()

# --- Static Files Setup ---
if os.path.exists(public_path):
    logger.info(f"Mounting static files from: {public_path}")
    assets_dir = os.path.join(public_path, "assets")
    if os.path.exists(assets_dir):
        app.mount("/public/assets", StaticFiles(directory=assets_dir), name="assets")
    
    @app.get("/")
    async def read_index():
        index_path = os.path.join(public_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path) as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>Index.html not found</h1>")

    @app.get("/{file_path:path}")
    async def serve_static(file_path: str):
        full_path = os.path.join(public_path, file_path)
        if os.path.isfile(full_path):
            return FileResponse(full_path)
        return {"error": "Not Found", "path": file_path}

@app.on_event("startup")
async def startup_event():
    logger.info("H-Bridge starting...")
    await redis_client.connect()
    asyncio.create_task(surreal_client.connect())
    # STORY 23.3: Start discovery worker
    asyncio.create_task(agent_discovery_worker())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("H-Bridge shutting down...")
    await redis_client.disconnect()
    await surreal_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
