import logging
import os
from typing import Optional

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.elevenlabs.io/v1"


class ElevenLabsProvider:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")

    async def synthesize(self, text: str, voice_id: str) -> bytes:
        if not HTTPX_AVAILABLE or not text or not self.api_key:
            return b""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{_BASE_URL}/text-to-speech/{voice_id}",
                    headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
                    json={"text": text, "model_id": "eleven_multilingual_v2"},
                    timeout=10.0,
                )
                return r.content if r.status_code == 200 else b""
        except Exception as e:
            logger.warning(f"ElevenLabsProvider: {e}")
            return b""
