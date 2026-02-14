import logging
from datetime import datetime

from src.infrastructure.redis import RedisClient

from .models import (
    INTERACTION_SCORES,
    RELATIONSHIP_THRESHOLDS,
    AgentRelationship,
    InteractionType,
    RelationshipStatus,
    ToneModifier,
    ToneType,
)
from .repository import RelationshipRepository

logger = logging.getLogger(__name__)


class AgentRelationshipService:
    def __init__(self, redis_client: RedisClient):
        self.repository = RelationshipRepository(redis_client)

    async def get_relationship(self, agent_a: str, agent_b: str) -> AgentRelationship:
        relationship = await self.repository.get(agent_a, agent_b)
        if relationship is None:
            relationship = AgentRelationship(agent_a=agent_a, agent_b=agent_b)
            await self.repository.save(relationship)
        return relationship

    async def record_interaction(
        self,
        agent_a: str,
        agent_b: str,
        interaction_type: InteractionType,
        context: str = "",
    ) -> AgentRelationship:
        relationship = await self.get_relationship(agent_a, agent_b)

        score_delta = INTERACTION_SCORES.get(interaction_type, 0)
        relationship.score += score_delta
        relationship.interaction_count += 1
        relationship.last_interaction = datetime.utcnow()
        relationship.updated_at = datetime.utcnow()

        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": interaction_type.value,
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
                f"Relationship evolved: {agent_a}-{agent_b} "
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

    def get_tone_modifier(self, relationship: AgentRelationship) -> ToneModifier:
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

    async def apply_tone_to_message(
        self,
        agent_from: str,
        agent_to: str,
        message: str,
    ) -> tuple[str, ToneModifier]:
        relationship = await self.get_relationship(agent_from, agent_to)
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
        
        modified_message = f"{prefix}{message}{suffix}"
        
        return modified_message, tone_mod

    async def get_all_relationships(self, agent_id: str) -> list[AgentRelationship]:
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
                        f"Relationship decayed: {rel.agent_a}-{rel.agent_b} "
                        f"{old_status.value} -> {rel.status.value}"
                    )
                
                rel.updated_at = datetime.utcnow()
                await self.repository.save(rel)
                updated += 1
        
        return updated
