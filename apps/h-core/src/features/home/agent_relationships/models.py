from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RelationshipStatus(str, Enum):
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    RIVAL = "rival"
    ALLY = "ally"
    ENEMY = "enemy"


class InteractionType(str, Enum):
    HELPFUL = "helpful"
    HURTFUL = "hurtful"
    NEUTRAL = "neutral"
    COLLABORATIVE = "collaborative"
    COMPETITIVE = "competitive"
    SOCIAL = "social"
    IGNORED = "ignored"


class ToneType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    WARM = "warm"
    COLD = "cold"
    HOSTILE = "hostile"
    FRIENDLY = "friendly"


RELATIONSHIP_THRESHOLDS = {
    RelationshipStatus.ENEMY: -60,
    RelationshipStatus.RIVAL: -40,
    RelationshipStatus.STRANGER: -20,
    RelationshipStatus.ACQUAINTANCE: 20,
    RelationshipStatus.FRIEND: 60,
    RelationshipStatus.ALLY: 80,
}

INTERACTION_SCORES = {
    InteractionType.HELPFUL: 10,
    InteractionType.COLLABORATIVE: 8,
    InteractionType.SOCIAL: 5,
    InteractionType.NEUTRAL: 0,
    InteractionType.IGNORED: -1,
    InteractionType.COMPETITIVE: -3,
    InteractionType.HURTFUL: -15,
}

TONE_MODIFIERS = {
    (RelationshipStatus.STRANGER, 0): ToneType.NEUTRAL,
    (RelationshipStatus.ACQUAINTANCE, 0): ToneType.NEUTRAL,
    (RelationshipStatus.FRIEND, 0): ToneType.WARM,
    (RelationshipStatus.ALLY, 0): ToneType.FRIENDLY,
    (RelationshipStatus.RIVAL, 0): ToneType.COLD,
    (RelationshipStatus.ENEMY, 0): ToneType.HOSTILE,
}


@dataclass
class AgentRelationship:
    agent_a: str
    agent_b: str
    score: float = 0.0
    status: RelationshipStatus = RelationshipStatus.STRANGER
    interaction_count: int = 0
    last_interaction: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    history: list[dict[str, Any]] = field(default_factory=list)

    def _get_status_key(self) -> RelationshipStatus:
        return self.status

    def get_tone(self) -> ToneType:
        base_tone = TONE_MODIFIERS.get((self._get_status_key(), 0), ToneType.NEUTRAL)
        
        if self.score > 30:
            if base_tone == ToneType.COLD:
                return ToneType.NEUTRAL
            if base_tone == ToneType.HOSTILE:
                return ToneType.COLD
        elif self.score < -30:
            if base_tone == ToneType.WARM:
                return ToneType.NEUTRAL
            if base_tone == ToneType.FRIENDLY:
                return ToneType.COLD
        
        return base_tone

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_a": self.agent_a,
            "agent_b": self.agent_b,
            "score": self.score,
            "status": self.status.value,
            "interaction_count": self.interaction_count,
            "last_interaction": self.last_interaction.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentRelationship":
        last_interaction = data.get("last_interaction")
        if isinstance(last_interaction, str):
            last_interaction = datetime.fromisoformat(last_interaction)
        elif last_interaction is None:
            last_interaction = datetime.utcnow()

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.utcnow()

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.utcnow()

        return cls(
            agent_a=data.get("agent_a", ""),
            agent_b=data.get("agent_b", ""),
            score=data.get("score", 0.0),
            status=RelationshipStatus(data.get("status", "stranger")),
            interaction_count=data.get("interaction_count", 0),
            last_interaction=last_interaction,
            created_at=created_at,
            updated_at=updated_at,
            history=data.get("history", []),
        )


@dataclass
class ToneModifier:
    tone: ToneType
    warmth_bonus: float = 0.0
    formality_bonus: float = 0.0
    empathy_bonus: float = 0.0
