from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_LOCK_KEY = "hairem:gpu:inference_lock"
_LOCK_TTL = 120


class InferenceLock:
    def __init__(self, redis_client: Any, ttl: int = _LOCK_TTL):
        self.redis = redis_client
        self.ttl = ttl
        self._token: str | None = None

    async def acquire(self, timeout: float = 30.0) -> bool:
        self._token = str(uuid.uuid4())
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            try:
                client = self.redis.client
                if client is None:
                    return True
                acquired = await client.set(_LOCK_KEY, self._token, nx=True, ex=self.ttl)
                if acquired:
                    logger.debug(f"InferenceLock: acquired ({self._token[:8]})")
                    return True
            except Exception as e:
                logger.warning(f"InferenceLock: acquire error — {e}")
                return True
            await asyncio.sleep(0.5)
        logger.warning("InferenceLock: acquire timeout — proceeding without lock")
        return False

    async def release(self) -> None:
        if self._token is None:
            return
        try:
            client = self.redis.client
            if client is None:
                return
            current = await client.get(_LOCK_KEY)
            if current and current.decode() == self._token:
                await client.delete(_LOCK_KEY)
                logger.debug(f"InferenceLock: released ({self._token[:8]})")
        except Exception as e:
            logger.warning(f"InferenceLock: release error — {e}")
        finally:
            self._token = None

    async def __aenter__(self) -> "InferenceLock":
        await self.acquire()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.release()
