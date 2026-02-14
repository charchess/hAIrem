from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class LocationConfidence(BaseModel):
    level: Literal["high", "medium", "low"] = Field(default="high", description="Confidence level of location")
    reason: Optional[str] = Field(default=None, description="Reason for confidence level")


class AgentLocation(BaseModel):
    agent_id: str = Field(..., min_length=1, description="Agent identifier")
    room_id: str = Field(..., min_length=1, description="Room identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Location timestamp")
    confidence: Optional[LocationConfidence] = Field(default=None, description="Location confidence")


class LocationHistoryQuery(BaseModel):
    agent_id: str = Field(..., min_length=1, description="Agent identifier")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of history entries")
