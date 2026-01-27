import asyncio
import os
import logging
from src.infrastructure.plugin_loader import PluginLoader, AgentRegistry
from src.infrastructure.redis import RedisClient
from src.infrastructure.llm import LlmClient
from src.infrastructure.surrealdb import SurrealDbClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BACKGROUND_AGENTS")

async def run():
    registry = AgentRegistry()
    redis_client = RedisClient(host="localhost")
    await redis_client.connect()
    
    llm_client = LlmClient()
    
    # Optional: Mock SurrealDB to avoid connection errors in logs
    surreal_client = SurrealDbClient(url="ws://localhost:8000", user="root", password="root")
    
    agents_dir = os.path.abspath("agents")
    loader = PluginLoader(agents_dir, registry, redis_client, llm_client, surreal_client)
    
    logger.info("Starting PluginLoader...")
    await loader.start()
    
    # Keep running
    await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run())
