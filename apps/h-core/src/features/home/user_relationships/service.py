import logging
import random
from datetime import datetime
from typing import Optional

from src.infrastructure.redis import RedisClient

from .models import (
    INTERACTION_SCORES,
    PREFERENCE_EXPRESSION_THRESHOLDS,
    RELATIONSHIP_THRESHOLDS,
    PreferenceExpression,
    PreferenceModifier,
    RelationshipStatus,
    ToneModifier,
    ToneType,
    UserRelationship,
)
from .repository import UserRelationshipRepository

logger = logging.getLogger(__name__)


class UserRelationshipService:
    PREFERENCE_MESSAGES = {
        PreferenceExpression.WANT_MORE_INTERACTION: [
            "Always nice to chat with you!",
            "Looking forward to our next conversation!",
            "Great talking with you again!",
            "We should do this more often!",
        ],
        PreferenceExpression.WANT_LESS_INTERACTION: [
            "I see.",
            "Alright then.",
            "Well, I have other things to attend to.",
            "I suppose that's all for now.",
        ],
    }

    def __init__(self, redis_client: RedisClient):
        self.repository = UserRelationshipRepository(redis_client)

    async def get_relationship(self, agent_id: str, user_id: str) -> UserRelationship:
        relationship = await self.repository.get(agent_id, user_id)
        if relationship is None:
            relationship = UserRelationship(agent_id=agent_id, user_id=user_id)
            await self.repository.save(relationship)
        return relationship

    async def record_interaction(
        self,
        agent_id: str,
        user_id: str,
        interaction_type,
        context: str = "",
    ) -> UserRelationship:
        relationship = await self.get_relationship(agent_id, user_id)

        score_delta = INTERACTION_SCORES.get(interaction_type, 0)
        relationship.score += score_delta
        relationship.interaction_count += 1
        relationship.last_interaction = datetime.utcnow()
        relationship.updated_at = datetime.utcnow()

        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": interaction_type.value if hasattr(interaction_type, 'value') else str(interaction_type),
            "score_delta": score_delta,
            "context": context,
            "new_score": relationship.score,
        }
        relationship.history.append(history_entry)
        if len(relationship.history) > 50:
            relationship.history = relationship.history[-50:]

        new_status = self._calculate_status(relationship.score)
        if new_status != relationship.status:
            logger.info(
                f"User relationship evolved: {agent_id}-{user_id} "
                f"{relationship.status.value} -> {new_status.value}"
            )
            relationship.status = new_status

        await self.repository.save(relationship)
        return relationship

    def _calculate_status(self, score: float) -> RelationshipStatus:
        if score >= RELATIONSHIP_THRESHOLDS[RelationshipStatus.ALLY]:
            return RelationshipStatus.ALLY
        elif score >= RELATIONSHIP_THRESHOLDS[RelationshipStatus.FRIEND]:
            return RelationshipStatus.FRIEND
        elif score >= RELATIONSHIP_THRESHOLDS[RelationshipStatus.ACQUAINTANCE]:
            return RelationshipStatus.ACQUAINTANCE
        elif score <= RELATIONSHIP_THRESHOLDS[RelationshipStatus.ENEMY]:
            return RelationshipStatus.ENEMY
        elif score <= RELATIONSHIP_THRESHOLDS[RelationshipStatus.RIVAL]:
            return RelationshipStatus.RIVAL
        elif score <= RELATIONSHIP_THRESHOLDS[RelationshipStatus.STRANGER]:
            return RelationshipStatus.STRANGER
        else:
            return RelationshipStatus.ACQUAINTANCE

    def get_tone_modifier(self, relationship: UserRelationship) -> ToneModifier:
        tone = relationship.get_tone()
        
        warmth = 0.0
        formality = 0.0
        empathy = 0.0

        if tone == ToneType.FRIENDLY:
            warmth = 0.5
            empathy = 0.3
        elif tone == ToneType.WARM:
            warmth = 0.3
            empathy = 0.2
        elif tone == ToneType.COLD:
            warmth = -0.3
            formality = 0.2
        elif tone == ToneType.HOSTILE:
            warmth = -0.5
            formality = 0.3

        return ToneModifier(
            tone=tone,
            warmth_bonus=warmth,
            formality_bonus=formality,
            empathy_bonus=empathy,
        )

    def get_preference_modifier(
        self,
        relationship: UserRelationship,
        include_subtle_hints: bool = False,
    ) -> PreferenceModifier:
        preference = relationship.get_preference_expression()
        
        if preference == PreferenceExpression.NONE:
            return PreferenceModifier(
                expression=PreferenceExpression.NONE,
                message_suffix="",
                include_subtle_hints=False,
            )
        
        message = ""
        if include_subtle_hints and random.random() < 0.3:
            messages = self.PREFERENCE_MESSAGES.get(preference, [])
            if messages:
                message = " " + random.choice(messages)
        
        return PreferenceModifier(
            expression=preference,
            message_suffix=message,
            include_subtle_hints=include_subtle_hints,
        )

    async def apply_tone_to_message(
        self,
        agent_id: str,
        user_id: str,
        message: str,
        include_preference: bool = False,
    ) -> tuple[str, ToneModifier, Optional[PreferenceModifier]]:
        relationship = await self.get_relationship(agent_id, user_id)
        tone_mod = self.get_tone_modifier(relationship)
        
        prefix = ""
        suffix = ""
        
        if tone_mod.tone == ToneType.FRIENDLY:
            prefix = "😊 "
        elif tone_mod.tone == ToneType.WARM:
            prefix = "🙂 "
        elif tone_mod.tone == ToneType.COLD:
            prefix = "🧊 "
        elif tone_mod.tone == ToneType.HOSTILE:
            prefix = "😒 "

        if tone_mod.formality_bonus > 0.2:
            suffix = "."

        pref_mod = None
        if include_preference:
            pref_mod = self.get_preference_modifier(relationship, include_subtle_hints=True)
            suffix += pref_mod.message_suffix
        
        modified_message = f"{prefix}{message}{suffix}"
        
        return modified_message, tone_mod, pref_mod

    async def get_all_relationships(self, agent_id: str) -> list[UserRelationship]:
        return await self.repository.get_all_for_agent(agent_id)

    async def decay_scores(self, decay_factor: float = 0.01) -> int:
        updated = 0
        relationships = await self.get_all_relationships("__all__")
        
        for rel in relationships:
            if rel.interaction_count < 3:
                continue
            
            days_since_interaction = (datetime.utcnow() - rel.last_interaction).days
            if days_since_interaction > 7:
                decay = decay_factor * days_since_interaction
                rel.score = max(-100, rel.score - decay)
                
                old_status = rel.status
                rel.status = self._calculate_status(rel.score)
                
                if old_status != rel.status:
                    logger.info(
                        f"User relationship decayed: {rel.agent_id}-{rel.user_id} "
                        f"{old_status.value} -> {rel.status.value}"
                    )
                
                rel.updated_at = datetime.utcnow()
                await self.repository.save(rel)
                updated += 1
        
        return updated

    async def classify_interaction(
        self,
        user_message: str,
        agent_response: str,
        sentiment_score: float,
    ) -> "InteractionType":
        from .models import InteractionType
        
        if sentiment_score > 0.5:
            return InteractionType.PLEASANT
        elif sentiment_score < -0.5:
            return InteractionType.UNPLEASANT
        elif "help" in user_message.lower() or "thanks" in user_message.lower():
            return InteractionType.HELPFUL
        elif "?" in user_message and len(user_message) < 50:
            return InteractionType.SOCIAL
        
        return InteractionType.NEUTRAL
