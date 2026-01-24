import hashlib
import json
import logging
import os
from typing import List, Optional
from src.infrastructure.redis import RedisClient

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Caches vector embeddings in Redis to reduce API costs and latency."""
    
    def __init__(self, redis_client: RedisClient, ttl: int = 604800):
        """
        Initialize the cache.
        :param redis_client: The existing Redis client.
        :param ttl: Time-to-live in seconds (default: 7 days).
        """
        self.redis = redis_client
        self.ttl = ttl
        self.prefix = "hairem:cache:emb:"

    def _get_key(self, text: str) -> str:
        """Generate a stable Redis key using SHA-256 hashing of the normalized text."""
        # Normalize: strip whitespace and lower case for better hit rate
        normalized = text.strip().lower()
        text_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        return f"{self.prefix}{text_hash}"

    async def get(self, text: str) -> Optional[List[float]]:
        """Retrieve an embedding from the cache."""
        key = self._get_key(text)
        try:
            # redis_client.client is the underlying redis-py instance
            data = await self.redis.client.get(key)
            if data:
                logger.debug(f"Cache hit for: {text[:30]}...")
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error reading from embedding cache: {e}")
        return None

    async def set(self, text: str, vector: List[float]):
        """Store an embedding in the cache."""
        if not vector:
            return
            
        key = self._get_key(text)
        try:
            await self.redis.client.set(key, json.dumps(vector), ex=self.ttl)
            logger.debug(f"Cache stored for: {text[:30]}...")
        except Exception as e:
            logger.error(f"Error writing to embedding cache: {e}")
