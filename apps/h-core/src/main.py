import asyncio
import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.infrastructure.redis import RedisClient
from src.infrastructure.plugin_loader import AgentRegistry, PluginLoader
from src.models.hlink import HLinkMessage

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.infrastructure.llm import LlmClient

app = FastAPI(title="hAIrem H-Core")

# Global instances
redis_client = RedisClient(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379))
)
llm_client = LlmClient()
agent_registry = AgentRegistry()
# Use absolute path or configurable path for agents
agents_path = os.getenv("AGENTS_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../agents")))
plugin_loader = PluginLoader(agents_dir=agents_path, registry=agent_registry, redis_client=redis_client, llm_client=llm_client)

@app.on_event("startup")
async def startup_event():
    logger.info("H-Core is starting up...")
    await redis_client.connect()
    await plugin_loader.start()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("H-Core is shutting down...")
    await redis_client.disconnect()
    plugin_loader.stop()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("New A2UI client connected via WebSocket.")
    
    # Event handler to push Redis messages to WebSocket
    async def redis_to_ws_handler(message: HLinkMessage):
        try:
            # We filter for narrative or system messages for the UI
            if message.type.startswith("narrative.") or message.type.startswith("system."):
                await websocket.send_json(message.model_dump())
        except Exception as e:
            logger.error(f"Failed to push message to WS: {e}")

    try:
        # Subscribe to broadcast and generic narrative channels
        # In a real app, we might subscribe to specific room channels
        await redis_client.subscribe("broadcast", redis_to_ws_handler)
        
        # Keep the connection alive
        while True:
            # We can also receive messages FROM the UI here (e.g. User text)
            data = await websocket.receive_json()
            logger.info(f"Received from UI: {data}")
            # In next stories, we would wrap this in HLink and publish to Redis
            
    except WebSocketDisconnect:
        logger.info("A2UI client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
