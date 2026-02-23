from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Episode:
    episode_id: str
    session_id: str
    agent_id: str
    user_id: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    summary: str | None = None
    emotion_arc: list[dict[str, Any]] = field(default_factory=list)
    fact_ids: list[str] = field(default_factory=list)

    def is_open(self) -> bool:
        return self.ended_at is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "summary": self.summary,
            "emotion_arc": self.emotion_arc,
            "fact_ids": self.fact_ids,
        }
