import logging
from typing import Optional

from src.services.audio.stt_service import SttService
from src.features.home.voice_recognition.service import VoiceRecognitionService
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

logger = logging.getLogger(__name__)


class AudioPipeline:
    def __init__(self, stt_service: SttService, voice_recognition: VoiceRecognitionService, redis_client):
        self.stt = stt_service
        self.voice_recognition = voice_recognition
        self.redis = redis_client

    async def process_audio_chunk(self, audio_bytes: bytes, session_id: str) -> Optional[str]:
        text = await self.stt.transcribe(audio_bytes)
        if not text:
            return None

        session_user = await self.voice_recognition.process_session_voice(session_id, audio_bytes)
        user_id = session_user.user_id if session_user and session_user.user_id else "anonymous"

        msg = HLinkMessage(
            type=MessageType.USER_MESSAGE,
            sender=Sender(agent_id=user_id, role="user"),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content={"text": text, "user_id": user_id, "session_id": session_id}),
        )
        await self.redis.publish_event("conversation_stream", msg.model_dump(mode="json"))
        return text
