from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict

class MessageType(str, Enum):
    NARRATIVE_TEXT = "narrative.text"
    NARRATIVE_CHUNK = "narrative.chunk"
    NARRATIVE_ACTION = "narrative.action"
    SYSTEM_LOG = "system.log"
    SYSTEM_STATUS_UPDATE = "system.status_update"
    EXPERT_COMMAND = "expert.command"
    EXPERT_RESPONSE = "expert.response"
    AGENT_INTERNAL_NOTE = "agent.internal_note"

class Priority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    SYSTEM = "system"

class Sender(BaseModel):
    agent_id: str
    role: str

class Recipient(BaseModel):
    target: str
    room: Optional[str] = None

class Payload(BaseModel):
    content: Any
    format: str = "text"
    emotion: Optional[str] = "neutral"

class Metadata(BaseModel):
    priority: Priority = Priority.NORMAL
    correlation_id: Optional[UUID] = None
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

    model_config = ConfigDict(use_enum_values=True)
