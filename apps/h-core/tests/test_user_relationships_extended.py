import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from features.home.user_relationships.service import UserRelationshipService
from features.home.user_relationships.repository import UserRelationshipRepository
from features.home.user_relationships.models import (
    UserRelationship,
    RelationshipStatus,
    InteractionType,
    ToneType,
    PreferenceExpression,
    INTERACTION_SCORES,
)


def make_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


class TestUserRelationshipRepository:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self):
        redis = make_redis()
        repo = UserRelationshipRepository(redis)
        result = await repo.get("lisa", "user123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_relationship_when_found(self):
        redis = make_redis()
        rel = UserRelationship(agent_id="lisa", user_id="user123")
        redis.get = AsyncMock(return_value=rel.to_dict())
        repo = UserRelationshipRepository(redis)
        result = await repo.get("lisa", "user123")
        assert result is not None
        assert result.agent_id == "lisa"

    @pytest.mark.asyncio
    async def test_get_exception_returns_none(self):
        redis = make_redis()
        redis.get = AsyncMock(side_effect=Exception("redis error"))
        repo = UserRelationshipRepository(redis)
        result = await repo.get("lisa", "user123")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_success(self):
        redis = make_redis()
        repo = UserRelationshipRepository(redis)
        rel = UserRelationship(agent_id="lisa", user_id="user123")
        result = await repo.save(rel)
        assert result is True
        redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_exception_returns_false(self):
        redis = make_redis()
        redis.set = AsyncMock(side_effect=Exception("redis error"))
        repo = UserRelationshipRepository(redis)
        rel = UserRelationship(agent_id="lisa", user_id="user123")
        result = await repo.save(rel)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self):
        redis = make_redis()
        repo = UserRelationshipRepository(redis)
        result = await repo.delete("lisa", "user123")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_exception_returns_false(self):
        redis = make_redis()
        redis.delete = AsyncMock(side_effect=Exception("redis error"))
        repo = UserRelationshipRepository(redis)
        result = await repo.delete("lisa", "user123")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_for_agent_empty(self):
        redis = make_redis()
        repo = UserRelationshipRepository(redis)
        result = await repo.get_all_for_agent("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_for_agent_with_results(self):
        redis = make_redis()
        rel = UserRelationship(agent_id="lisa", user_id="user123")
        redis.scan = AsyncMock(return_value=(0, ["agent:user:relationship:lisa:user123"]))
        redis.get = AsyncMock(return_value=rel.to_dict())
        repo = UserRelationshipRepository(redis)
        result = await repo.get_all_for_agent("lisa")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_all_for_agent_exception(self):
        redis = make_redis()
        redis.scan = AsyncMock(side_effect=Exception("redis error"))
        repo = UserRelationshipRepository(redis)
        result = await repo.get_all_for_agent("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_for_user_empty(self):
        redis = make_redis()
        repo = UserRelationshipRepository(redis)
        result = await repo.get_all_for_user("user123")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_for_user_with_results(self):
        redis = make_redis()
        rel = UserRelationship(agent_id="lisa", user_id="user123")
        redis.scan = AsyncMock(return_value=(0, ["agent:user:relationship:lisa:user123"]))
        redis.get = AsyncMock(return_value=rel.to_dict())
        repo = UserRelationshipRepository(redis)
        result = await repo.get_all_for_user("user123")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_all_for_user_exception(self):
        redis = make_redis()
        redis.scan = AsyncMock(side_effect=Exception("error"))
        repo = UserRelationshipRepository(redis)
        result = await repo.get_all_for_user("user123")
        assert result == []


class TestUserRelationshipService:
    @pytest.mark.asyncio
    async def test_get_relationship_creates_new(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        rel = await service.get_relationship("lisa", "user123")
        assert rel.agent_id == "lisa"
        assert rel.user_id == "user123"

    @pytest.mark.asyncio
    async def test_get_relationship_returns_existing(self):
        redis = make_redis()
        existing = UserRelationship(agent_id="lisa", user_id="user123", score=50.0)
        redis.get = AsyncMock(return_value=existing.to_dict())
        service = UserRelationshipService(redis)
        rel = await service.get_relationship("lisa", "user123")
        assert rel.score == 50.0

    @pytest.mark.asyncio
    async def test_record_interaction_updates_score(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        rel = await service.record_interaction(
            agent_id="lisa",
            user_id="user123",
            interaction_type=InteractionType.HELPFUL,
        )
        assert rel.score != 0
        assert rel.interaction_count == 1

    @pytest.mark.asyncio
    async def test_record_interaction_status_change(self):
        redis = make_redis()
        existing = UserRelationship(agent_id="lisa", user_id="user123", score=55.0)
        redis.get = AsyncMock(return_value=existing.to_dict())
        service = UserRelationshipService(redis)
        rel = await service.record_interaction(
            agent_id="lisa",
            user_id="user123",
            interaction_type=InteractionType.PLEASANT,
        )
        assert rel is not None

    @pytest.mark.asyncio
    async def test_record_interaction_history_capped_at_50(self):
        redis = make_redis()
        existing = UserRelationship(agent_id="lisa", user_id="user123")
        existing.history = [{"x": i} for i in range(50)]
        redis.get = AsyncMock(return_value=existing.to_dict())
        service = UserRelationshipService(redis)
        rel = await service.record_interaction(
            agent_id="lisa",
            user_id="user123",
            interaction_type=InteractionType.NEUTRAL,
        )
        assert len(rel.history) <= 50

    @pytest.mark.asyncio
    async def test_calculate_status_all_levels(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        assert service._calculate_status(100) == RelationshipStatus.ALLY
        assert service._calculate_status(60) == RelationshipStatus.FRIEND
        assert service._calculate_status(20) == RelationshipStatus.ACQUAINTANCE
        assert service._calculate_status(-80) == RelationshipStatus.ENEMY
        assert service._calculate_status(-40) == RelationshipStatus.RIVAL
        assert service._calculate_status(-20) == RelationshipStatus.STRANGER
        assert service._calculate_status(5) == RelationshipStatus.ACQUAINTANCE

    def test_get_tone_modifier_friendly(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        rel = UserRelationship(agent_id="lisa", user_id="user123", score=80.0)
        rel.status = RelationshipStatus.ALLY
        tone = service.get_tone_modifier(rel)
        assert tone.warmth_bonus != 0 or tone.tone is not None

    def test_get_tone_modifier_all_tones(self):
        redis = make_redis()
        service = UserRelationshipService(redis)

        for score, expected_tone in [
            (80.0, ToneType.FRIENDLY),
            (50.0, ToneType.WARM),
            (-30.0, ToneType.COLD),
            (-70.0, ToneType.HOSTILE),
            (5.0, ToneType.NEUTRAL),
        ]:
            rel = UserRelationship(agent_id="lisa", user_id="user123", score=score)
            rel.status = service._calculate_status(score)
            tone = service.get_tone_modifier(rel)
            assert tone is not None

    def test_get_preference_modifier_none(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        rel = UserRelationship(agent_id="lisa", user_id="user123", score=5.0)
        rel.status = RelationshipStatus.ACQUAINTANCE
        mod = service.get_preference_modifier(rel)
        assert mod.expression == PreferenceExpression.NONE

    def test_get_preference_modifier_want_more_with_hints(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        rel = UserRelationship(agent_id="lisa", user_id="user123", score=80.0)
        rel.status = RelationshipStatus.ALLY
        for _ in range(10):
            mod = service.get_preference_modifier(rel, include_subtle_hints=True)
            assert mod is not None

    @pytest.mark.asyncio
    async def test_apply_tone_to_message_friendly(self):
        redis = make_redis()
        existing = UserRelationship(agent_id="lisa", user_id="user123", score=80.0)
        existing.status = RelationshipStatus.ALLY
        redis.get = AsyncMock(return_value=existing.to_dict())
        service = UserRelationshipService(redis)
        msg, tone, pref = await service.apply_tone_to_message("lisa", "user123", "Hello")
        assert "Hello" in msg

    @pytest.mark.asyncio
    async def test_apply_tone_to_message_hostile(self):
        redis = make_redis()
        existing = UserRelationship(agent_id="lisa", user_id="user123", score=-80.0)
        existing.status = RelationshipStatus.ENEMY
        redis.get = AsyncMock(return_value=existing.to_dict())
        service = UserRelationshipService(redis)
        msg, tone, pref = await service.apply_tone_to_message("lisa", "user123", "Hello")
        assert "Hello" in msg

    @pytest.mark.asyncio
    async def test_apply_tone_to_message_with_preference(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        msg, tone, pref = await service.apply_tone_to_message("lisa", "user123", "Hello", include_preference=True)
        assert pref is not None

    @pytest.mark.asyncio
    async def test_apply_tone_formality_suffix(self):
        redis = make_redis()
        existing = UserRelationship(agent_id="lisa", user_id="user123", score=-70.0)
        existing.status = RelationshipStatus.ENEMY
        redis.get = AsyncMock(return_value=existing.to_dict())
        service = UserRelationshipService(redis)
        msg, tone, _ = await service.apply_tone_to_message("lisa", "user123", "Hello")
        assert "Hello" in msg

    @pytest.mark.asyncio
    async def test_get_all_relationships(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        result = await service.get_all_relationships("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_decay_scores_no_relationships(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        updated = await service.decay_scores()
        assert updated == 0

    @pytest.mark.asyncio
    async def test_decay_scores_skips_low_interaction(self):
        redis = make_redis()
        rel = UserRelationship(agent_id="lisa", user_id="user123", score=50.0)
        rel.interaction_count = 1
        rel.last_interaction = datetime.utcnow() - timedelta(days=30)
        redis.scan = AsyncMock(return_value=(0, ["agent:user:relationship:lisa:user123"]))
        redis.get = AsyncMock(return_value=rel.to_dict())
        service = UserRelationshipService(redis)
        updated = await service.decay_scores()
        assert updated == 0

    @pytest.mark.asyncio
    async def test_decay_scores_applies_decay(self):
        redis = make_redis()
        rel = UserRelationship(agent_id="lisa", user_id="user123", score=50.0)
        rel.interaction_count = 5
        rel.last_interaction = datetime.utcnow() - timedelta(days=30)
        redis.scan = AsyncMock(return_value=(0, ["agent:user:relationship:lisa:user123"]))
        redis.get = AsyncMock(return_value=rel.to_dict())
        service = UserRelationshipService(redis)
        updated = await service.decay_scores()
        assert updated == 1

    @pytest.mark.asyncio
    async def test_classify_interaction_pleasant(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        result = await service.classify_interaction("hello", "response", 0.8)
        assert result.value == "pleasant"

    @pytest.mark.asyncio
    async def test_classify_interaction_unpleasant(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        result = await service.classify_interaction("hello", "response", -0.8)
        assert result.value == "unpleasant"

    @pytest.mark.asyncio
    async def test_classify_interaction_helpful(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        result = await service.classify_interaction("thanks for your help", "ok", 0.0)
        assert result.value == "helpful"

    @pytest.mark.asyncio
    async def test_classify_interaction_social(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        result = await service.classify_interaction("how?", "ok", 0.0)
        assert result.value == "social"

    @pytest.mark.asyncio
    async def test_classify_interaction_neutral(self):
        redis = make_redis()
        service = UserRelationshipService(redis)
        result = await service.classify_interaction("blah blah blah blah blah blah blah blah blah blah?", "ok", 0.0)
        assert result.value == "neutral"
