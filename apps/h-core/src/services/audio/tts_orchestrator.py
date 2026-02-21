import base64
import logging

from src.services.audio.melotts_provider import MeloTtsProvider
from src.services.audio.elevenlabs_provider import ElevenLabsProvider

logger = logging.getLogger(__name__)


class TtsOrchestrator:
    def __init__(self, primary: MeloTtsProvider, fallback: ElevenLabsProvider, redis_client):
        self.primary = primary
        self.fallback = fallback
        self.redis = redis_client

    async def synthesize(self, text: str, voice_id: str = "FR", timeout_ms: int = 800) -> bytes:
        audio = await self.primary.synthesize(text, voice_id, timeout_ms)
        if not audio:
            logger.info("TtsOrchestrator: primary empty, using fallback.")
            audio = await self.fallback.synthesize(text, voice_id)
        return audio

    async def synthesize_and_broadcast(self, text: str, agent_id: str, voice_id: str = "FR") -> None:
        audio = await self.synthesize(text, voice_id)
        if not audio:
            return
        chunk = base64.b64encode(audio).decode()
        event = {
            "type": "audio.chunk",
            "sender": {"agent_id": agent_id, "role": "agent"},
            "payload": {"content": {"audio_b64": chunk, "agent_id": agent_id}},
        }
        try:
            await self.redis.publish_event("system_stream", event)
        except Exception as e:
            logger.error(f"TtsOrchestrator: broadcast error — {e}")
