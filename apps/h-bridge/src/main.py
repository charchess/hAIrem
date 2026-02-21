import asyncio
import json
import logging
import os
import sys
from uuid import UUID, uuid4

# Pathing
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
core_src = os.path.abspath(os.path.join(current_dir, "../../h-core/src"))
if core_src not in sys.path:
    sys.path.insert(0, core_src)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from infrastructure.redis import RedisClient
from infrastructure.surrealdb import SurrealDbClient
from models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender

# Services
from services.voice import voice_profile_service
from services.voice_modulation import voice_modulation_service
from services.prosody import prosody_service

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("BRIDGE")

app = FastAPI(title="hAIrem Bridge")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Paths
public_path = os.getenv("STATIC_PATH", "/app/static")
agents_path = os.getenv("AGENTS_PATH", "/app/agents")

# Global
discovered_agents = {}
active_connections = set()
last_heartbeat = None
redis_client = RedisClient(host=os.getenv("REDIS_HOST", "redis"))
surreal_client = SurrealDbClient(
    url=os.getenv("SURREALDB_URL", "ws://surrealdb:8000/rpc"), user="root", password="root"
)


async def system_stream_worker():
    logger.info("📡 BRIDGE: Stream worker ready.")

    async def handler(data: dict):
        global last_heartbeat
        try:
            msg_type = data.get("type")
            # 1. Broadcast to ALL WebSockets
            msg_json = json.dumps(data)
            for ws in list(active_connections):
                try:
                    await ws.send_text(msg_json)
                except:
                    if ws in active_connections:
                        active_connections.remove(ws)

            # 2. Extract Heartbeat Bundle
            if msg_type == "system.heartbeat":
                last_heartbeat = data
                # logger.info(f"💓 HEARTBEAT: Received and broadcasted. Brain state: {data.get('payload', {}).get('content', {}).get('health', {}).get('brain')}")
                payload = data.get("payload", {})
                if isinstance(payload, str):
                    payload = json.loads(payload)
                content = payload.get("content", {})
                if isinstance(content, str):
                    content = json.loads(content)

                # Update Discovery Cache
                agents = content.get("agents", {})
                for aid, stats in agents.items():
                    discovered_agents[aid] = {
                        "id": aid,
                        "active": stats.get("active"),
                        "llm_model": stats.get("llm_model"),
                        "total_tokens": stats.get("tokens"),
                        "prompt_tokens": stats.get("prompt_tokens"),
                        "completion_tokens": stats.get("completion_tokens"),
                        "cost": stats.get("cost"),
                        "location": stats.get("location"),
                        "preferred_location": stats.get("preferred_location"),
                        "skills": stats.get("skills"),
                    }
        except Exception as e:
            logger.error(f"BRIDGE_WORKER_ERR: {e}")

    await redis_client.listen_stream("system_stream", f"bridge-{uuid4().hex[:4]}", "bridge-1", handler, start_id="$")


@app.on_event("startup")
async def startup():
    await redis_client.connect()
    await surreal_client.connect()
    await voice_profile_service.initialize()
    await voice_modulation_service.initialize()
    await prosody_service.initialize()
    asyncio.create_task(system_stream_worker())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    if last_heartbeat:
        await websocket.send_text(json.dumps(last_heartbeat))
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"📥 BRIDGE: Received from UI: {data[:100]}...")
            msg = json.loads(data)
            stream = (
                "system_stream"
                if "admin" in msg.get("type", "") or "config" in msg.get("type", "")
                else "conversation_stream"
            )
            logger.info(f"🚀 BRIDGE: Publishing to {stream}")
            await redis_client.publish_event(stream, msg)
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WS_ERR: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/api/agents")
async def get_agents():
    return list(discovered_agents.values())


@app.get("/api/config")
async def get_config():
    # 1. Try SurrealDB
    db_config = await surreal_client.get_config("system")
    if db_config:
        llm = db_config.get("llm_config", {})
        return {"llm_model": llm.get("model"), "llm_provider": llm.get("provider"), "source": "db"}

    # 2. Fallback to Env
    model = os.getenv("LLM_MODEL", "openrouter/nvidia/nemotron-3-nano-30b-a3b:free")
    provider = "openai"
    if "openrouter" in model.lower() or os.getenv("OPENROUTER_API_KEY"):
        provider = "openrouter"
    elif "ollama" in model.lower():
        provider = "ollama"
    elif "google" in model.lower():
        provider = "google"
    return {"llm_model": model, "llm_provider": provider, "source": "env"}


@app.get("/api/history")
async def get_history():
    if not surreal_client.client:
        return {"messages": [], "status": "connecting"}
    try:
        res = await surreal_client._call("query", "SELECT * FROM fact ORDER BY created_at DESC LIMIT 50;")
        messages = res[0].get("result", []) if res else []
        return {"messages": messages, "status": "ok"}
    except Exception as e:
        logger.error(f"History fail: {e}")
        return {"messages": [], "status": "error"}


@app.get("/", response_class=HTMLResponse)
async def root():
    with open(os.path.join(public_path, "index.html"), "r") as f:
        return f.read()


app.mount("/static", StaticFiles(directory=public_path), name="static")
app.mount("/agents", StaticFiles(directory=agents_path), name="agents")


@app.get("/api/status")
async def get_status():
    return {"status": "ok", "heartbeat": last_heartbeat, "agents": len(discovered_agents)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
