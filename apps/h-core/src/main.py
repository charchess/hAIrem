import os
import asyncio
import logging
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient
from src.infrastructure.llm import LlmClient
from src.infrastructure.plugin_loader import PluginLoader, AgentRegistry
from src.models.hlink import HLinkMessage, Sender, Recipient

# Logging setup
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="hAIrem Core")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
agents_path = os.getenv("AGENTS_PATH", "/app/agents")
public_path = "/app/a2ui"

# Infrastructure Clients
redis_client = RedisClient(host=os.getenv("REDIS_HOST", "localhost"))
surreal_client = SurrealDbClient(
    url=os.getenv("SURREALDB_URL", "ws://surrealdb:8000/rpc"),
    user=os.getenv("SURREALDB_USER", "root"),
    password=os.getenv("SURREALDB_PASS", "root")
)
llm_client = LlmClient()
agent_registry = AgentRegistry()
plugin_loader = PluginLoader(agents_path, agent_registry, redis_client, llm_client, surreal_client)

# Static Files Setup
if os.path.exists(public_path):
    logger.info(f"Mounting static files from: {public_path}")
    assets_dir = os.path.join(public_path, "assets")
    if os.path.exists(assets_dir):
        app.mount("/public/assets", StaticFiles(directory=assets_dir), name="assets")
    
    @app.get("/")
    async def read_index():
        index_path = os.path.join(public_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>Index.html not found</h1>")

    @app.get("/{file_path:path}")
    async def serve_static(file_path: str):
        full_path = os.path.join(public_path, file_path)
        if os.path.isfile(full_path):
            return FileResponse(full_path)
        return {"error": "Not Found", "path": file_path}

# API Endpoints
@app.get("/api/agents")
async def get_agents():
    agents = []
    for agent_id, agent in agent_registry.agents.items():
        agents.append({
            "id": agent_id,
            "commands": list(agent.commands.keys())
        })
    return agents

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

@app.on_event("startup")
async def startup_event():
    logger.info("H-Core starting startup sequence...")
    await redis_client.connect()
    # Non-blocking SurrealDB connection
    asyncio.create_task(surreal_client.connect())
    await plugin_loader.start()
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("H-Core is shutting down...")
    # Safe close
    if hasattr(redis_client, 'disconnect'): await redis_client.disconnect()
    elif hasattr(redis_client, 'close'): await redis_client.close()
    await surreal_client.close()

# WebSocket Bridge
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
            data = await websocket.receive_json()
            msg_type = data.get("type")
            msg_id = data.get("id", str(asyncio.get_event_loop().time()))
            
            # Construct standard message object
            sender = Sender(agent_id="user", role="user")
            
            if msg_type == "narrative.text":
                # Frontend sends payload nested, but we need to robustly handle flat or nested
                payload = data.get("payload", {})
                content = payload.get("content") if isinstance(payload, dict) else data.get("content")
                
                # Determine target from recipient if present
                recipient = data.get("recipient", {})
                target = recipient.get("target") if isinstance(recipient, dict) else data.get("target", "Renarde")

                hlink_msg = HLinkMessage(
                    id=msg_id,
                    type="narrative.text",
                    sender=sender,
                    recipient=Recipient(target=target),
                    payload={"content": content}
                )
                await redis_client.publish(f"agent:{target}", hlink_msg)
            
            elif msg_type == "expert.command":
                payload = data.get("payload", {})
                # Try getting command from nested content first, then from payload directly
                content_dict = payload.get("content", {}) if isinstance(payload.get("content"), dict) else {}
                command = content_dict.get("command") or payload.get("command") or data.get("command")
                args = content_dict.get("args") or payload.get("args") or data.get("args") or ""
                
                recipient = data.get("recipient", {})
                target = recipient.get("target") if isinstance(recipient, dict) else data.get("agent_id", "Renarde")

                hlink_msg = HLinkMessage(
                    id=msg_id,
                    type="expert.command",
                    sender=sender,
                    recipient=Recipient(target=target),
                    payload={
                        "content": None,  # Satisfy Pydantic model requirement
                        "command": command,
                        "args": args
                    }
                )
                await redis_client.publish(f"agent:{target}", hlink_msg)

            # Story 11.4: Persist user messages (needs dict for SurrealDB)
            asyncio.create_task(surreal_client.persist_message(hlink_msg.model_dump()))

    except WebSocketDisconnect:
        logger.info("A2UI client disconnected.")
    finally:
        stop_event.set()
        rtw_task.cancel()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
