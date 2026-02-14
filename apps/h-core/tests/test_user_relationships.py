import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from features.home.user_relationships import (
    UserRelationship,
    UserRelationshipService,
    InteractionType,
    UserRelationshipRepository,
    RelationshipStatus,
    ToneModifier,
    ToneType,
    PreferenceExpression,
    PreferenceModifier,
    INTERACTION_SCORES,
    RELATIONSHIP_THRESHOLDS,
    PREFERENCE_EXPRESSION_THRESHOLDS,
)


class TestUserRelationship:
    def test_to_dict(self):
        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=25.0,
            status=RelationshipStatus.FRIEND,
            interaction_count=5,
        )

        data = rel.to_dict()

        assert data["agent_id"] == "lisa"
        assert data["user_id"] == "user123"
        assert data["score"] == 25.0
        assert data["status"] == "friend"
        assert data["interaction_count"] == 5

    def test_from_dict(self):
        data = {
            "agent_id": "lisa",
            "user_id": "user456",
            "score": -30.0,
            "status": "rival",
            "interaction_count": 3,
            "last_interaction": "2024-01-15T10:30:00",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-15T10:30:00",
            "history": [],
        }

        rel = UserRelationship.from_dict(data)

        assert rel.agent_id == "lisa"
        assert rel.user_id == "user456"
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


class TestPreferenceExpressionThresholds:
    def test_preference_thresholds(self):
        assert PREFERENCE_EXPRESSION_THRESHOLDS[PreferenceExpression.WANT_MORE_INTERACTION] > 0
        assert PREFERENCE_EXPRESSION_THRESHOLDS[PreferenceExpression.WANT_LESS_INTERACTION] < 0


class TestInteractionScores:
    def test_positive_interactions(self):
        assert INTERACTION_SCORES[InteractionType.HELPFUL] > 0
        assert INTERACTION_SCORES[InteractionType.COLLABORATIVE] > 0
        assert INTERACTION_SCORES[InteractionType.SOCIAL] > 0
        assert INTERACTION_SCORES[InteractionType.PLEASANT] > 0

    def test_negative_interactions(self):
        assert INTERACTION_SCORES[InteractionType.HURTFUL] < 0
        assert INTERACTION_SCORES[InteractionType.COMPETITIVE] < 0
        assert INTERACTION_SCORES[InteractionType.UNPLEASANT] < 0

    def test_neutral_interactions(self):
        assert INTERACTION_SCORES[InteractionType.NEUTRAL] == 0
        assert INTERACTION_SCORES[InteractionType.IGNORED] < 0


class TestToneType:
    def test_get_tone_friend(self):
        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=50.0,
            status=RelationshipStatus.FRIEND,
        )
        assert rel.get_tone() == ToneType.WARM

    def test_get_tone_ally(self):
        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=80.0,
            status=RelationshipStatus.ALLY,
        )
        assert rel.get_tone() == ToneType.FRIENDLY

    def test_get_tone_rival(self):
        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=-50.0,
            status=RelationshipStatus.RIVAL,
        )
        assert rel.get_tone() == ToneType.COLD

    def test_get_tone_enemy(self):
        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=-80.0,
            status=RelationshipStatus.ENEMY,
        )
        assert rel.get_tone() == ToneType.HOSTILE


class TestPreferenceExpression:
    def test_want_more_interaction(self):
        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=80.0,
            status=RelationshipStatus.ALLY,
        )
        assert rel.get_preference_expression() == PreferenceExpression.WANT_MORE_INTERACTION

    def test_want_less_interaction(self):
        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=-80.0,
            status=RelationshipStatus.ENEMY,
        )
        assert rel.get_preference_expression() == PreferenceExpression.WANT_LESS_INTERACTION

    def test_no_preference(self):
        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=0.0,
            status=RelationshipStatus.STRANGER,
        )
        assert rel.get_preference_expression() == PreferenceExpression.NONE


class TestUserRelationshipRepository:
    @pytest.mark.asyncio
    async def test_get_key(self):
        mock_redis = AsyncMock()
        repo = UserRelationshipRepository(mock_redis)

        key = repo._get_key("lisa", "user123")
        assert "user123" in key
        assert "lisa" in key


class TestUserRelationshipService:
    @pytest.mark.asyncio
    async def test_calculate_status(self):
        mock_redis = AsyncMock()
        service = UserRelationshipService(mock_redis)

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
        service = UserRelationshipService(mock_redis)

        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=80.0,
            status=RelationshipStatus.ALLY,
        )

        tone_mod = service.get_tone_modifier(rel)
        assert tone_mod.tone == ToneType.FRIENDLY
        assert tone_mod.warmth_bonus > 0

    @pytest.mark.asyncio
    async def test_get_tone_modifier_hostile(self):
        mock_redis = AsyncMock()
        service = UserRelationshipService(mock_redis)

        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=-80.0,
            status=RelationshipStatus.ENEMY,
        )

        tone_mod = service.get_tone_modifier(rel)
        assert tone_mod.tone == ToneType.HOSTILE
        assert tone_mod.warmth_bonus < 0

    @pytest.mark.asyncio
    async def test_get_preference_modifier_want_more(self):
        mock_redis = AsyncMock()
        service = UserRelationshipService(mock_redis)

        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=80.0,
            status=RelationshipStatus.ALLY,
        )

        pref_mod = service.get_preference_modifier(rel, include_subtle_hints=True)
        assert pref_mod.expression == PreferenceExpression.WANT_MORE_INTERACTION

    @pytest.mark.asyncio
    async def test_get_preference_modifier_want_less(self):
        mock_redis = AsyncMock()
        service = UserRelationshipService(mock_redis)

        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=-80.0,
            status=RelationshipStatus.ENEMY,
        )

        pref_mod = service.get_preference_modifier(rel, include_subtle_hints=True)
        assert pref_mod.expression == PreferenceExpression.WANT_LESS_INTERACTION

    @pytest.mark.asyncio
    async def test_get_preference_modifier_none(self):
        mock_redis = AsyncMock()
        service = UserRelationshipService(mock_redis)

        rel = UserRelationship(
            agent_id="lisa",
            user_id="user123",
            score=0.0,
            status=RelationshipStatus.STRANGER,
        )

        pref_mod = service.get_preference_modifier(rel, include_subtle_hints=True)
        assert pref_mod.expression == PreferenceExpression.NONE

    @pytest.mark.asyncio
    async def test_record_interaction_creates_relationship(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        
        service = UserRelationshipService(mock_redis)
        
        rel = await service.record_interaction(
            agent_id="lisa",
            user_id="user123",
            interaction_type=InteractionType.HELPFUL,
            context="User asked for help",
        )
        
        assert rel.agent_id == "lisa"
        assert rel.user_id == "user123"
        assert rel.score == 10
        assert rel.interaction_count == 1
        assert rel.status == RelationshipStatus.ACQUAINTANCE
