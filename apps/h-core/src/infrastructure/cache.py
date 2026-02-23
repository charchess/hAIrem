import hashlib
import logging

from src.infrastructure.redis import RedisClient

logger = logging.getLogger(__name__)


class EmbeddingCache:
    def __init__(self, redis_client: RedisClient, ttl: int = 604800):
        self.redis = redis_client
        self.ttl = ttl
        self.prefix = "hairem:cache:emb:"

    def _get_key(self, text: str, model_name: str) -> str:
        normalized = text.strip().lower()
        text_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        safe_model = model_name.replace("/", "_").replace(":", "_")
        return f"{self.prefix}{safe_model}:{text_hash}"

    async def get(self, text: str, model_name: str) -> list[float] | None:
        key = self._get_key(text, model_name)
        try:
            data = await self.redis.get(key)
            if data is not None:
                logger.debug(f"Cache hit for: {text[:30]}...")
                return data if isinstance(data, list) else None
        except Exception as e:
            logger.error(f"Error reading from embedding cache: {e}")
        return None

    async def set(self, text: str, vector: list[float], model_name: str) -> None:
        if not vector:
            return
        key = self._get_key(text, model_name)
        try:
            await self.redis.set(key, vector, ex=self.ttl)
            logger.debug(f"Cache stored for: {text[:30]}...")
        except Exception as e:
            logger.error(f"Error writing to embedding cache: {e}")
