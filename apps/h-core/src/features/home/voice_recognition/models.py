from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import numpy as np


class VoiceProfile(BaseModel):
    user_id: str
    name: str
    embedding: list[float] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sample_count: int = 0
    is_active: bool = True


class VoiceIdentificationResult(BaseModel):
    identified: bool
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    confidence: float = 0.0
    matched_profile: Optional[VoiceProfile] = None
    embedding: Optional[list[float]] = None


class VoiceEnrollmentRequest(BaseModel):
    user_id: str
    name: str
    audio_data: bytes


class VoiceIdentificationRequest(BaseModel):
    session_id: str
    audio_data: bytes


class SessionUser(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    identified_at: Optional[datetime] = None
    is_anonymous: bool = True
