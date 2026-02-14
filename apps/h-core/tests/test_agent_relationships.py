import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from features.home.agent_relationships import (
    AgentRelationship,
    AgentRelationshipService,
    InteractionType,
    RelationshipRepository,
    RelationshipStatus,
    ToneModifier,
    ToneType,
    INTERACTION_SCORES,
    RELATIONSHIP_THRESHOLDS,
)


class TestAgentRelationship:
    def test_to_dict(self):
        rel = AgentRelationship(
            agent_a="lisa",
            agent_b="electra",
            score=25.0,
            status=RelationshipStatus.FRIEND,
            interaction_count=5,
        )

        data = rel.to_dict()

        assert data["agent_a"] == "lisa"
        assert data["agent_b"] == "electra"
        assert data["score"] == 25.0
        assert data["status"] == "friend"
        assert data["interaction_count"] == 5

    def test_from_dict(self):
        data = {
            "agent_a": "renarde",
            "agent_b": "dieu",
            "score": -30.0,
            "status": "rival",
            "interaction_count": 3,
            "last_interaction": "2024-01-15T10:30:00",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-15T10:30:00",
            "history": [],
        }

        rel = AgentRelationship.from_dict(data)

        assert rel.agent_a == "renarde"
        assert rel.agent_b == "dieu"
        assert rel.score == -30.0
        assert rel.status == RelationshipStatus.RIVAL
        assert rel.interaction_count == 3


class TestRelationshipStatus:
    def test_thresholds_order(self):
        assert RELATIONSHIP_THRESHOLDS[RelationshipStatus.ENEMY] < RELATIONSHIP_THRESHOLDS[RelationshipStatus.RIVAL]
        assert RELATIONSHIP_THRESHOLDS[RelationshipStatus.RIVAL] < RELATIONSHIP_THRESHOLDS[RelationshipStatus.STRANGER]
        assert RELATIONSHIP_THRESHOLDS[RelationshipStatus.STRANGER] < RELATIONSHIP_THRESHOLDS[RelationshipStatus.ACQUAINTANCE]
        assert RELATIONSHIP_THRESHOLDS[RelationshipStatus.ACQUAINTANCE] < RELATIONSHIP_THRESHOLDS[RelationshipStatus.FRIEND]
        assert RELATIONSHIP_THRESHOLDS[RelationshipStatus.FRIEND] < RELATIONSHIP_THRESHOLDS[RelationshipStatus.ALLY]


class TestInteractionScores:
    def test_positive_interactions(self):
        assert INTERACTION_SCORES[InteractionType.HELPFUL] > 0
        assert INTERACTION_SCORES[InteractionType.COLLABORATIVE] > 0
        assert INTERACTION_SCORES[InteractionType.SOCIAL] > 0

    def test_negative_interactions(self):
        assert INTERACTION_SCORES[InteractionType.HURTFUL] < 0
        assert INTERACTION_SCORES[InteractionType.COMPETITIVE] < 0

    def test_neutral_interactions(self):
        assert INTERACTION_SCORES[InteractionType.NEUTRAL] == 0
        assert INTERACTION_SCORES[InteractionType.IGNORED] < 0


class TestToneType:
    def test_get_tone_friend(self):
        rel = AgentRelationship(
            agent_a="lisa",
            agent_b="electra",
            score=50.0,
            status=RelationshipStatus.FRIEND,
        )
        assert rel.get_tone() == ToneType.WARM

    def test_get_tone_ally(self):
        rel = AgentRelationship(
            agent_a="lisa",
            agent_b="electra",
            score=80.0,
            status=RelationshipStatus.ALLY,
        )
        assert rel.get_tone() == ToneType.FRIENDLY

    def test_get_tone_rival(self):
        rel = AgentRelationship(
            agent_a="lisa",
            agent_b="electra",
            score=-50.0,
            status=RelationshipStatus.RIVAL,
        )
        assert rel.get_tone() == ToneType.COLD

    def test_get_tone_enemy(self):
        rel = AgentRelationship(
            agent_a="lisa",
            agent_b="electra",
            score=-80.0,
            status=RelationshipStatus.ENEMY,
        )
        assert rel.get_tone() == ToneType.HOSTILE


class TestRelationshipRepository:
    @pytest.mark.asyncio
    async def test_get_key(self):
        mock_redis = AsyncMock()
        repo = RelationshipRepository(mock_redis)

        key = repo._get_key("lisa", "electra")
        assert "electra" in key
        assert "lisa" in key

    @pytest.mark.asyncio
    async def test_get_key_symmetric(self):
        mock_redis = AsyncMock()
        repo = RelationshipRepository(mock_redis)

        key1 = repo._get_key("lisa", "electra")
        key2 = repo._get_key("electra", "lisa")
        assert key1 == key2


class TestAgentRelationshipService:
    @pytest.mark.asyncio
    async def test_calculate_status(self):
        mock_redis = AsyncMock()
        service = AgentRelationshipService(mock_redis)

        assert service._calculate_status(85) == RelationshipStatus.ALLY
        assert service._calculate_status(70) == RelationshipStatus.FRIEND
        assert service._calculate_status(30) == RelationshipStatus.ACQUAINTANCE
        assert service._calculate_status(0) == RelationshipStatus.ACQUAINTANCE
        assert service._calculate_status(-10) == RelationshipStatus.ACQUAINTANCE
        assert service._calculate_status(-30) == RelationshipStatus.STRANGER
        assert service._calculate_status(-50) == RelationshipStatus.RIVAL
        assert service._calculate_status(-70) == RelationshipStatus.ENEMY

    @pytest.mark.asyncio
    async def test_get_tone_modifier_friendly(self):
        mock_redis = AsyncMock()
        service = AgentRelationshipService(mock_redis)

        rel = AgentRelationship(
            agent_a="lisa",
            agent_b="electra",
            score=80.0,
            status=RelationshipStatus.ALLY,
        )

        tone_mod = service.get_tone_modifier(rel)
        assert tone_mod.tone == ToneType.FRIENDLY
        assert tone_mod.warmth_bonus > 0

    @pytest.mark.asyncio
    async def test_get_tone_modifier_hostile(self):
        mock_redis = AsyncMock()
        service = AgentRelationshipService(mock_redis)

        rel = AgentRelationship(
            agent_a="lisa",
            agent_b="electra",
            score=-80.0,
            status=RelationshipStatus.ENEMY,
        )

        tone_mod = service.get_tone_modifier(rel)
        assert tone_mod.tone == ToneType.HOSTILE
        assert tone_mod.warmth_bonus < 0
