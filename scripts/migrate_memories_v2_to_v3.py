import asyncio
import os
import logging
from src.infrastructure.surrealdb import SurrealDbClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate():
    # Load env vars or use defaults
    url = os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc")
    user = os.getenv("SURREALDB_USER", "root")
    password = os.getenv("SURREALDB_PASS", "root")
    
    client = SurrealDbClient(url, user, password)
    await client.connect()
    
    if not client.client:
        logger.error("Failed to connect to SurrealDB")
        return

    logger.info("Fetching old memories...")
    try:
        # 1. Retrieve all from old memories table
        res = await client._call('query', "SELECT * FROM memories;")
        old_memories = []
        if res and isinstance(res, list) and len(res) > 0:
            old_memories = res[0].get("result", []) if isinstance(res[0], dict) else res
        
        logger.info(f"Found {len(old_memories)} memories to migrate.")
        
        # 2. Iterate and insert into graph
        count = 0
        for mem in old_memories:
            # Re-map fields if necessary
            fact_data = {
                "fact": mem.get("fact"),
                "subject": mem.get("subject", "user"),
                "agent": mem.get("agent", "system"),
                "confidence": mem.get("confidence", 1.0),
                "embedding": mem.get("embedding", [])
            }
            
            if fact_data["fact"]:
                await client.insert_graph_memory(fact_data)
                count += 1
        
        logger.info(f"Migration complete. {count} memories moved to graph model.")
        
        # 3. Optional: Cleanup old table?
        # Let's keep it for safety for now.
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
