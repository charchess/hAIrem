import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

MELOTTS_BASE_URL = os.getenv("MELOTTS_BASE_URL", "http://melotts-openvoice:8008")


class OpenVoiceClient:
    def __init__(self, base_url: str = MELOTTS_BASE_URL, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def clone_voice(
        self,
        audio_bytes: bytes,
        reference_path: str,
        tone: float = 0.0,
        speed: float = 1.0,
    ) -> Optional[bytes]:
        try:
            with open(reference_path, "rb") as ref_f:
                files = {
                    "audio_file": ("input.wav", audio_bytes, "audio/wav"),
                    "reference_audio": ("reference.wav", ref_f.read(), "audio/wav"),
                }
            resp = httpx.post(
                f"{self.base_url}/clone",
                files=files,
                data={"tone": str(tone), "speed": str(speed)},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.content
        except FileNotFoundError:
            logger.warning(f"OpenVoice reference not found: {reference_path}. Returning base audio.")
            return audio_bytes
        except Exception as e:
            logger.error(f"OpenVoice cloning failed: {e}")
            return None
