import base64
import logging
import time

from src.services.audio.melotts_provider import MeloTtsProvider
from src.services.audio.elevenlabs_provider import ElevenLabsProvider
from src.infrastructure.metrics import get_metrics_collector

logger = logging.getLogger(__name__)


class TtsOrchestrator:
    def __init__(self, primary: MeloTtsProvider, fallback: ElevenLabsProvider, redis_client, room_router=None):
        self.primary = primary
        self.fallback = fallback
        self.redis = redis_client
        self.room_router = room_router

    async def synthesize(self, text: str, voice_id: str = "FR", timeout_ms: int = 800) -> bytes:
        _t0 = time.monotonic()
        audio = await self.primary.synthesize(text, voice_id, timeout_ms)
        if not audio:
            logger.info("TtsOrchestrator: primary empty, using fallback.")
            audio = await self.fallback.synthesize(text, voice_id)
        get_metrics_collector().record_tts_synthesis(time.monotonic() - _t0)
        return audio

    async def synthesize_and_broadcast(
        self, text: str, agent_id: str, voice_id: str = "FR", room_id: str | None = None
    ) -> None:
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
        if self.room_router and room_id:
            try:
                await self.room_router.route(f"data:audio/mp3;base64,{chunk}", room_id=room_id, agent_id=agent_id)
            except Exception as e:
                logger.error(f"TtsOrchestrator: room routing error — {e}")
