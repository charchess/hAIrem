import logging
import os
from typing import Optional

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


class MeloTtsProvider:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("MELOTTS_URL", "http://melotts:5000")

    async def synthesize(self, text: str, voice_id: str = "FR", timeout_ms: int = 800) -> bytes:
        if not HTTPX_AVAILABLE or not text:
            return b""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{self.base_url}/synthesize",
                    json={"text": text, "voice_id": voice_id},
                    timeout=timeout_ms / 1000,
                )
                return r.content if r.status_code == 200 else b""
        except Exception as e:
            logger.warning(f"MeloTtsProvider: {e}")
            return b""
