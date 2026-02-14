from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AgentInterests(BaseModel):
    topics: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)


class AgentEmotionalCapabilities(BaseModel):
    supported_emotions: list[str] = Field(default_factory=list)
    emotional_range: list[str] = Field(default_factory=list)
    empathy_level: float = 0.5
    adaptability: float = 0.5


class AgentEmotionalState(BaseModel):
    current_emotion: str = "neutral"
    emotion_intensity: float = 0.0
    emotional_history: list[dict] = Field(default_factory=list)
    interactions_count: int = 0
    last_emotion_change: Optional[datetime] = None


class AgentProfile(BaseModel):
    agent_id: str
    name: str
    role: str
    description: str | None = None
    interests: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    expertise: list[str] = Field(default_factory=list)
    personality_traits: list[str] = Field(default_factory=list)
    emotional_capabilities: AgentEmotionalCapabilities = Field(default_factory=AgentEmotionalCapabilities)
    is_active: bool = True
    priority_weight: float = 1.0
    last_response_time: Optional[float] = None
    response_count: int = 0
