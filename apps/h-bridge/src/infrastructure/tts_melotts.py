import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

MELOTTS_BASE_URL = os.getenv("MELOTTS_BASE_URL", "http://melotts-openvoice:8008")


class MeloTTSClient:
    def __init__(self, base_url: str = MELOTTS_BASE_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def synthesize(self, text: str, language: str = "FR", speed: float = 1.0) -> Optional[bytes]:
        try:
            resp = httpx.post(
                f"{self.base_url}/tts",
                json={"text": text, "language": language, "speed": speed},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            logger.error(f"MeloTTS synthesis failed: {e}")
            return None

    def health_check(self) -> bool:
        try:
            resp = httpx.get(f"{self.base_url}/health", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
