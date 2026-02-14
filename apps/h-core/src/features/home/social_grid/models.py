from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class NotificationType(str, Enum):
    STATUS_UPGRADE = "status_upgrade"
    STATUS_DOWNGRADE = "status_downgrade"
    SCORE_SIGNIFICANT_CHANGE = "score_significant_change"
    NEW_RELATIONSHIP = "new_relationship"
    RELATIONSHIP_ENDED = "relationship_ended"


class ChangeMagnitude(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


SIGNIFICANT_SCORE_CHANGE = 20
MAJOR_SCORE_CHANGE = 40
CRITICAL_SCORE_CHANGE = 60


INTERACTION_SCORES = {
    "helpful": 10,
    "collaborative": 8,
    "social": 5,
    "pleasant": 6,
    "neutral": 0,
    "ignored": -1,
    "competitive": -3,
    "hurtful": -15,
    "unpleasant": -8,
}


@dataclass
class RelationshipChangeEvent:
    relationship_type: str
    party_a: str
    party_b: str
    old_status: Optional[str]
    new_status: Optional[str]
    old_score: float
    new_score: float
    change_magnitude: ChangeMagnitude
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_type": self.relationship_type,
            "party_a": self.party_a,
            "party_b": self.party_b,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "old_score": self.old_score,
            "new_score": self.new_score,
            "change_magnitude": self.change_magnitude.value,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RelationshipChangeEvent":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()

        return cls(
            relationship_type=data.get("relationship_type", ""),
            party_a=data.get("party_a", ""),
            party_b=data.get("party_b", ""),
            old_status=data.get("old_status"),
            new_status=data.get("new_status"),
            old_score=data.get("old_score", 0.0),
            new_score=data.get("new_score", 0.0),
            change_magnitude=ChangeMagnitude(data.get("change_magnitude", "minor")),
            timestamp=timestamp,
        )


@dataclass
class RelationshipNotification:
    notification_type: NotificationType
    recipient_id: str
    recipient_type: str
    event: RelationshipChangeEvent
    message: str
    read: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "notification_type": self.notification_type.value,
            "recipient_id": self.recipient_id,
            "recipient_type": self.recipient_type,
            "event": self.event.to_dict(),
            "message": self.message,
            "read": self.read,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RelationshipNotification":
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.utcnow()

        event_data = data.get("event", {})
        if isinstance(event_data, dict):
            event = RelationshipChangeEvent.from_dict(event_data)
        else:
            event = None

        return cls(
            notification_type=NotificationType(data.get("notification_type", "status_upgrade")),
            recipient_id=data.get("recipient_id", ""),
            recipient_type=data.get("recipient_type", "agent"),
            event=event,
            message=data.get("message", ""),
            read=data.get("read", False),
            created_at=created_at,
        )


@dataclass
class SocialGridState:
    agent_user_relationships_count: int = 0
    agent_agent_relationships_count: int = 0
    pending_notifications: int = 0
    last_evolution_timestamp: Optional[datetime] = None
    loaded_from_db: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_user_relationships_count": self.agent_user_relationships_count,
            "agent_agent_relationships_count": self.agent_agent_relationships_count,
            "pending_notifications": self.pending_notifications,
            "last_evolution_timestamp": self.last_evolution_timestamp.isoformat() if self.last_evolution_timestamp else None,
            "loaded_from_db": self.loaded_from_db,
        }
