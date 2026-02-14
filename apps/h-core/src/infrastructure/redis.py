import asyncio
import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any, Optional, Dict

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.redis_url = f"redis://{host}:{port}/{db}"
        self.client: Optional[redis.Redis] = None
        self._stop_event = asyncio.Event()

    async def connect(self, timeout: int = 10):
        """Connect to Redis with exponential backoff and global timeout."""
        start_time = asyncio.get_event_loop().time()
        attempt = 0
        while not self._stop_event.is_set():
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.error(f"Redis connection timed out after {timeout}s")
                return False
            try:
                self.client = redis.from_url(self.redis_url, decode_responses=True)
                await self.client.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
                return True
            except Exception as e:
                attempt += 1
                wait_time = min(2**attempt, 5)
                logger.warning(f"Redis connection attempt {attempt} failed: {e}. Retrying...")
                await asyncio.sleep(wait_time)
        return False

    async def publish_event(self, stream: str, data: Dict[str, Any], max_len: int = 1000):
        """
        Add an event to a Redis Stream. 
        Supports both flattened dicts and wrapped messages for compatibility.
        """
        if not self.client:
            if not await self.connect(): return
        
        try:
            # Ensure we are passing a dict
            if not isinstance(data, dict):
                logger.error(f"publish_event: expected dict data, got {type(data)}")
                return

            # Flatten dict for Redis Stream (only strings/bytes supported as keys/values)
            payload = {}
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    payload[k] = json.dumps(v)
                else:
                    payload[k] = str(v)
            
            # XADD
            await self.client.xadd(stream, payload, maxlen=max_len, approximate=True)
            logger.debug(f"REDIS_STREAM_ADD: {stream}")
        except Exception as e:
            logger.error(f"Failed to add to stream {stream}: {e}")

    async def listen_stream(self, stream: str, group: str, consumer: str, handler: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]):
        """Consume messages from a Stream using a Consumer Group."""
        if not self.client:
            if not await self.connect(): return

        # Create group if not exists
        # FIX: Use id="$" to start from end of stream (only new messages)
        # This prevents replay of old messages on new connections
        try:
            await self.client.xgroup_create(stream, group, id="$", mkstream=True)
        except redis.ResponseError as e:
            if "already exists" not in str(e):
                logger.error(f"Failed to create group {group}: {e}")
                return

        while not self._stop_event.is_set():
            try:
                messages = await self.client.xreadgroup(group, consumer, {stream: ">"}, count=1, block=1000)
                
                if messages:
                    for s_name, msgs in messages:
                        for m_id, m_data in msgs:
                            try:
                                # De-serialize values
                                decoded_data = {}
                                for k, v in m_data.items():
                                    if isinstance(v, str) and (v.startswith('{') or v.startswith('[')):
                                        try:
                                            decoded_data[k] = json.loads(v)
                                        except:
                                            decoded_data[k] = v
                                    else:
                                        decoded_data[k] = v
                                
                                # Compatibility Check: If it's a wrapped message {"type": ..., "data": "..."}
                                if "data" in decoded_data and "type" in decoded_data and len(decoded_data) == 2:
                                    if isinstance(decoded_data["data"], dict):
                                        decoded_data = decoded_data["data"]
                                
                                # Process
                                await handler(decoded_data)
                                
                                # ACK
                                await self.client.xack(stream, group, m_id)
                                
                            except Exception as e:
                                logger.error(f"STREAM_PROC_FAIL on {stream}:{m_id}: {e}")
                
            except redis.ConnectionError:
                logger.error("Redis connection lost in stream listener. Re-connecting...")
                await self.connect()
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"Stream loop error: {e}")
                    await asyncio.sleep(2)

    async def disconnect(self):
        self._stop_event.set()
        if self.client:
            await self.client.aclose()
            logger.info("Redis connection closed.")

    async def publish(self, channel: str, message: Any):
        """Legacy Pub/Sub support."""
        if not self.client: await self.connect()
        try:
            # Handle both HLinkMessage objects and dicts
            if hasattr(message, 'model_dump_json'):
                data = message.model_dump_json()
            elif isinstance(message, dict):
                data = json.dumps(message)
            else:
                data = str(message)
                
            await self.client.publish(channel, data)
        except Exception as e:
            logger.error(f"Legacy publish failed: {e}")

    async def subscribe(self, channel: str, handler: Callable[[Any], Coroutine[Any, Any, None]]):
        """Legacy Pub/Sub support."""
        while not self._stop_event.is_set():
            try:
                if not self.client: await self.connect()
                async with self.client.pubsub() as pubsub:
                    await pubsub.subscribe(channel)
                    while not self._stop_event.is_set():
                        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                        if msg and msg["type"] == "message":
                            try:
                                data = json.loads(msg["data"])
                                # Try to validate as HLinkMessage for backward compatibility
                                if isinstance(data, dict):
                                    try:
                                        # Use model_validate instead of trying to access .type on a dict
                                        hlink_msg = HLinkMessage.model_validate(data)
                                        await handler(hlink_msg)
                                    except Exception as e:
                                        # If it's just a dict but not a full HLinkMessage
                                        await handler(data)
                                else:
                                    await handler(data)
                            except Exception as e:
                                logger.error(f"Legacy sub message parsing fail: {e}")

                                logger.error(f"Legacy sub fail: {e}")
            except Exception:
                await asyncio.sleep(1)
