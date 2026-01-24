import asyncio
import json
import logging
import time
from typing import Callable, Coroutine, Any
import redis.asyncio as redis
from src.models.hlink import HLinkMessage

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.redis_url = f"redis://{host}:{port}/{db}"
        self.client: Optional[redis.Redis] = None
        self._stop_event = asyncio.Event()

    async def connect(self):
        """Connect to Redis with exponential backoff."""
        attempt = 0
        while not self._stop_event.is_set():
            try:
                self.client = redis.from_url(self.redis_url, decode_responses=True)
                await self.client.ping()
                logger.info(f"Successfully connected to Redis at {self.redis_url}")
                return
            except Exception as e:
                attempt += 1
                wait_time = min(2**attempt, 30)
                logger.error(f"Failed to connect to Redis (attempt {attempt}): {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

    async def publish(self, channel: str, message: HLinkMessage):
        """Publish an H-Link message to a specific channel."""
        if not self.client:
            await self.connect()
        
        try:
            serialized_msg = message.model_dump_json()
            await self.client.publish(channel, serialized_msg)
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            # Potential retry logic here if needed

    async def subscribe(self, channel: str, handler: Callable[[HLinkMessage], Coroutine[Any, Any, None]]):
        """Subscribe to a channel and process messages using the provided handler."""
        while not self._stop_event.is_set():
            try:
                if not self.client:
                    await self.connect()
                
                async with self.client.pubsub() as pubsub:
                    await pubsub.subscribe(channel)
                    logger.info(f"Subscribed to channel: {channel}")
                    
                    while not self._stop_event.is_set():
                        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                        if message and message["type"] == "message":
                            logger.info(f"DEBUG REDIS: Raw data on {channel}: {message['data'][:100]}...")
                            try:
                                data = json.loads(message["data"])
                                hlink_msg = HLinkMessage.model_validate(data)
                                await handler(hlink_msg)
                            except Exception as e:
                                logger.error(f"Error processing message data: {e}")
            except redis.ConnectionError:
                logger.error("Redis connection lost. Attempting to reconnect...")
                self.client = None
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Unexpected error in subscription loop: {e}")
                await asyncio.sleep(5)

    async def disconnect(self):
        self._stop_event.set()
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed.")
