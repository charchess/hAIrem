import asyncio
import logging
import os
import tempfile
from typing import Optional, Any

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel

    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. STT disabled.")


class SttService:
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        self.model_size = model_size
        self.device = device
        self._model: Optional[Any] = None
        if FASTER_WHISPER_AVAILABLE:
            try:
                self._model = WhisperModel(model_size, device=device, compute_type="int8")
                logger.info(f"SttService: Whisper '{model_size}' loaded.")
            except Exception as e:
                logger.error(f"SttService: Model load failed — {e}")

    async def transcribe(self, audio_bytes: bytes, language: str = "fr") -> str:
        if not self._model or not audio_bytes:
            return ""
        try:
            loop = asyncio.get_running_loop()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                tmp_path = f.name

            def _run():
                segments, _ = self._model.transcribe(tmp_path, language=language)
                return " ".join(seg.text for seg in segments).strip()

            result = await loop.run_in_executor(None, _run)
            os.unlink(tmp_path)
            return result
        except Exception as e:
            logger.error(f"SttService: transcribe error — {e}")
            return ""

    async def transcribe_and_publish(
        self, audio_bytes: bytes, session_id: str, redis_client, language: str = "fr"
    ) -> Optional[str]:
        text = await self.transcribe(audio_bytes, language)
        if not text:
            return None
        from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

        msg = HLinkMessage(
            type=MessageType.USER_MESSAGE,
            sender=Sender(agent_id=session_id, role="user"),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content=text),
        )
        await redis_client.publish_event("conversation_stream", msg.model_dump(mode="json"))
        return text
