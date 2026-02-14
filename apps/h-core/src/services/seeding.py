import logging
from typing import Any, Dict, List
from src.infrastructure.surrealdb import SurrealDbClient
from src.infrastructure.redis import RedisClient

logger = logging.getLogger(__name__)

class SeedingService:
    def __init__(self, surreal: SurrealDbClient, redis: RedisClient):
        self.surreal = surreal
        self.redis = redis

    async def seed_graph(self, data: Dict[str, Any]):
        """
        Injects facts and relationships into SurrealDB.
        Expected format:
        {
            "subjects": [{"name": "Lisa"}, ...],
            "facts": [{"fact": "...", "subject": "Lisa", "agent": "system", "confidence": 1.0}, ...]
        }
        """
        logger.info("SEEDING: Starting graph injection...")
        
        # 1. Subjects
        for sub in data.get("subjects", []):
            name = sub.get("name")
            if name:
                sid = f"subject:`{name.lower().replace(' ', '_')}`"
                await self.surreal._call('query', 
                    f"INSERT INTO subject (id, name) VALUES ({sid}, $name) ON DUPLICATE KEY UPDATE name = $name;", 
                    {"name": name}
                )

        # 2. Facts (via our existing transactional method)
        for fact in data.get("facts", []):
            await self.surreal.insert_graph_memory(fact)
            
        logger.info("SEEDING: Graph injection complete.")

    async def reset_streams(self, streams: List[str]):
        """Deletes specified Redis streams."""
        if not self.redis.client:
            await self.redis.connect()
            
        for s in streams:
            logger.info(f"SEEDING: Resetting stream {s}")
            await self.redis.client.delete(s)
