from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class MessageType(str, Enum):
    USER_MESSAGE = "user_message"
    NARRATIVE_TEXT = "narrative.text"
    NARRATIVE_CHUNK = "narrative.chunk"
    NARRATIVE_ACTION = "narrative.action"
    SYSTEM_LOG = "system.log"
    SYSTEM_STATUS_UPDATE = "system.status_update"
    SYSTEM_CONFIG_UPDATE = "system.config_update"
    EXPERT_COMMAND = "expert.command"
    EXPERT_RESPONSE = "expert.response"
    AGENT_INTERNAL_NOTE = "agent.internal_note"
    VISUAL_ASSET = "visual.asset"
    VISUAL_RAW_PROMPT = "visual.raw_prompt"
    # Audio processing message types
    USER_AUDIO = "user_audio"
    AUDIO_PROCESSING_REQUEST = "audio_processing_request"
    AUDIO_RECEIVED = "audio_received"
    AUDIO_ERROR = "audio_error"
    STT_COMPLETE = "stt_complete"
    AUDIO_SESSION_REQUEST = "audio_session_request"
    AUDIO_SESSION_RESPONSE = "audio_session_response"
    # Wake word engine message types
    WAKE_WORD_DETECTED = "wake_word_detected"
    AUDIO_AUTO_START = "audio_auto_start"
    WAKE_WORD_STATUS = "wake_word_status"
    # Transcription update messages
    TRANSCRIPTION_UPDATE = "transcription_update"
    TRANSCRIPTION_ERROR = "transcription_error"
    TRANSCRIPTION_STATUS = "transcription_status"
    TRANSCRIPTION = "transcription" # Added for compatibility
    # TTS messages
    TTS_REQUEST = "tts_request"
    TTS_AUDIO_CHUNK = "tts_audio_chunk"
    TTS_START = "tts_start"
    TTS_END = "tts_end"
    TTS_ERROR = "tts_error"

class Priority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    SYSTEM = "system"

class Sender(BaseModel):
    agent_id: str
    role: str

class Recipient(BaseModel):
    target: str
    room: str | None = None

class Payload(BaseModel):
    content: Any
    text: Optional[str] = None
    format: str = "text"
    emotion: str | None = "neutral"
    # Audio-specific fields
    sample_rate: Optional[int] = None
    source: Optional[str] = None
    duration: Optional[Any] = None
    error_type: Optional[str] = None
    session_id: Optional[str] = None
    status: Optional[str] = None
    # Wake word specific fields
    confidence: Optional[float] = None
    wake_word: Optional[str] = None
    detection_time: Optional[str] = None
    trigger_source: Optional[str] = None
    enabled: Optional[bool] = None
    active: Optional[bool] = None

class Metadata(BaseModel):
    priority: Priority = Priority.NORMAL
    correlation_id: UUID | None = None
    ttl: int = Field(default=5, description="Prevent infinite loops")

class HLinkMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: MessageType
    sender: Sender
    recipient: Recipient
    payload: Payload
    metadata: Metadata = Field(default_factory=Metadata)

    @classmethod
    def validate_message(cls, data: dict):
        """Helper to validate message and return errors if any."""
        try:
            return cls.model_validate(data), None
        except Exception as e:
            return None, str(e)

    model_config = ConfigDict(
        use_enum_values=True,
        extra="allow",
        arbitrary_types_allowed=True,
        populate_by_name=True
    )
