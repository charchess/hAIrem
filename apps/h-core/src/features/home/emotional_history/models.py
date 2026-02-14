from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EmotionalStateRecord:
    emotion: str
    intensity: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    keywords: list[str] = field(default_factory=list)
    context: str = ""
    user_id: str = ""
    agent_id: str = "system"

    def to_dict(self) -> dict[str, Any]:
        return {
            "emotion": self.emotion,
            "intensity": self.intensity,
            "timestamp": self.timestamp.isoformat(),
            "keywords": self.keywords,
            "context": self.context,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmotionalStateRecord":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()
        
        return cls(
            emotion=data.get("emotion", "neutral"),
            intensity=data.get("intensity", 0.0),
            timestamp=timestamp,
            keywords=data.get("keywords", []),
            context=data.get("context", ""),
            user_id=data.get("user_id", ""),
            agent_id=data.get("agent_id", "system"),
        )


@dataclass
class EmotionalSummary:
    user_id: str
    period_start: datetime
    period_end: datetime
    emotion_counts: dict[str, int]
    dominant_emotion: str
    average_intensity: float
    summary_text: str
    archived_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "emotion_counts": self.emotion_counts,
            "dominant_emotion": self.dominant_emotion,
            "average_intensity": self.average_intensity,
            "summary_text": self.summary_text,
            "archived_at": self.archived_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmotionalSummary":
        return cls(
            user_id=data.get("user_id", ""),
            period_start=datetime.fromisoformat(data["period_start"]) if "period_start" in data else datetime.utcnow(),
            period_end=datetime.fromisoformat(data["period_end"]) if "period_end" in data else datetime.utcnow(),
            emotion_counts=data.get("emotion_counts", {}),
            dominant_emotion=data.get("dominant_emotion", "neutral"),
            average_intensity=data.get("average_intensity", 0.0),
            summary_text=data.get("summary_text", ""),
            archived_at=datetime.fromisoformat(data["archived_at"]) if "archived_at" in data else datetime.utcnow(),
        )
