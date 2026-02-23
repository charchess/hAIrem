import logging
import os
from typing import Optional

from infrastructure.tts_melotts import MeloTTSClient
from infrastructure.voice_openvoice import OpenVoiceClient

logger = logging.getLogger(__name__)

MELOTTS_BASE_URL = os.getenv("MELOTTS_BASE_URL", "http://melotts-openvoice:8008")
AGENTS_PATH = os.getenv("AGENTS_PATH", "/app/agents")


def _load_agent_voice_config(agent_id: str) -> dict:
    import yaml

    persona_path = os.path.join(AGENTS_PATH, agent_id.lower(), "persona.yaml")
    try:
        with open(persona_path) as f:
            persona = yaml.safe_load(f) or {}
        return persona.get("voice_config", {})
    except Exception:
        return {}


class TtsOrchestrator:
    def __init__(self) -> None:
        self.melo = MeloTTSClient(MELOTTS_BASE_URL)
        self.openvoice = OpenVoiceClient(MELOTTS_BASE_URL)

    def synthesize(self, text: str, agent_id: str, voice_config: Optional[dict] = None) -> Optional[bytes]:
        if voice_config is None:
            voice_config = _load_agent_voice_config(agent_id)

        language: str = voice_config.get("language", "FR")
        speed: float = float(voice_config.get("speed", 1.0))
        tone: float = float(voice_config.get("tone", 0.0))
        voice_ref: str = voice_config.get("voice_ref", "")

        audio_bytes = self.melo.synthesize(text, language=language, speed=speed)
        if not audio_bytes:
            return None

        if voice_ref:
            ref_path = voice_ref if os.path.isabs(voice_ref) else os.path.join(AGENTS_PATH, voice_ref)
            if os.path.exists(ref_path):
                cloned = self.openvoice.clone_voice(audio_bytes, ref_path, tone=tone, speed=speed)
                if cloned:
                    audio_bytes = cloned

        return audio_bytes

    def is_available(self) -> bool:
        return self.melo.health_check()


_tts_orchestrator: Optional[TtsOrchestrator] = None


def get_tts_orchestrator() -> TtsOrchestrator:
    global _tts_orchestrator
    if _tts_orchestrator is None:
        _tts_orchestrator = TtsOrchestrator()
    return _tts_orchestrator
