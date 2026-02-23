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
        assert (
            RELATIONSHIP_THRESHOLDS[RelationshipStatus.STRANGER]
            < RELATIONSHIP_THRESHOLDS[RelationshipStatus.ACQUAINTANCE]
        )
        assert (
            RELATIONSHIP_THRESHOLDS[RelationshipStatus.ACQUAINTANCE]
            < RELATIONSHIP_THRESHOLDS[RelationshipStatus.FRIEND]
        )
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

    @pytest.mark.asyncio
    async def test_get_relationship_creates_if_absent(self):
        """get_relationship creates and saves a new relationship when none exists."""
        mock_redis = MagicMock()
        service = AgentRelationshipService(mock_redis)

        service.repository.get = AsyncMock(return_value=None)
        service.repository.save = AsyncMock()

        rel = await service.get_relationship("lisa", "electra")

        assert rel.agent_a == "lisa"
        assert rel.agent_b == "electra"
        service.repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_relationship_returns_existing(self):
        """get_relationship returns the cached relationship when it exists."""
        mock_redis = MagicMock()
        service = AgentRelationshipService(mock_redis)

        existing = AgentRelationship(agent_a="lisa", agent_b="electra", score=40.0, status=RelationshipStatus.FRIEND)
        service.repository.get = AsyncMock(return_value=existing)
        service.repository.save = AsyncMock()

        rel = await service.get_relationship("lisa", "electra")

        assert rel.score == 40.0
        service.repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_record_interaction_updates_score(self):
        """record_interaction adds score_delta and persists."""
        mock_redis = MagicMock()
        service = AgentRelationshipService(mock_redis)

        initial = AgentRelationship(agent_a="a", agent_b="b", score=0.0)
        service.repository.get = AsyncMock(return_value=initial)
        service.repository.save = AsyncMock()

        rel = await service.record_interaction("a", "b", InteractionType.HELPFUL, "helped with task")

        assert rel.score == INTERACTION_SCORES[InteractionType.HELPFUL]
        assert rel.interaction_count == 1
        assert len(rel.history) == 1
        assert rel.history[0]["type"] == "helpful"
        service.repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_interaction_caps_history_at_50(self):
        """History is capped at 50 entries."""
        mock_redis = MagicMock()
        service = AgentRelationshipService(mock_redis)

        existing = AgentRelationship(agent_a="a", agent_b="b")
        existing.history = [{"ts": i} for i in range(55)]
        service.repository.get = AsyncMock(return_value=existing)
        service.repository.save = AsyncMock()

        await service.record_interaction("a", "b", InteractionType.NEUTRAL)

        assert len(existing.history) == 50

    @pytest.mark.asyncio
    async def test_record_interaction_evolves_status(self):
        """Status changes when score crosses a threshold."""
        mock_redis = MagicMock()
        service = AgentRelationshipService(mock_redis)

        # Start just below FRIEND threshold (60)
        existing = AgentRelationship(agent_a="a", agent_b="b", score=55.0, status=RelationshipStatus.ACQUAINTANCE)
        service.repository.get = AsyncMock(return_value=existing)
        service.repository.save = AsyncMock()

        rel = await service.record_interaction("a", "b", InteractionType.HELPFUL)  # +10 → 65

        assert rel.status == RelationshipStatus.FRIEND

    @pytest.mark.asyncio
    async def test_apply_tone_to_message_friendly_prefix(self):
        """Friendly tone prepends emoji."""
        mock_redis = MagicMock()
        service = AgentRelationshipService(mock_redis)

        rel = AgentRelationship(agent_a="a", agent_b="b", score=90.0, status=RelationshipStatus.ALLY)
        service.repository.get = AsyncMock(return_value=rel)
        service.repository.save = AsyncMock()

        msg, tone_mod = await service.apply_tone_to_message("a", "b", "Hello")

        assert "😊" in msg
        assert "Hello" in msg

    @pytest.mark.asyncio
    async def test_apply_tone_to_message_hostile_prefix(self):
        """Hostile tone prepends cold emoji and adds period."""
        mock_redis = MagicMock()
        service = AgentRelationshipService(mock_redis)

        rel = AgentRelationship(agent_a="a", agent_b="b", score=-80.0, status=RelationshipStatus.ENEMY)
        service.repository.get = AsyncMock(return_value=rel)
        service.repository.save = AsyncMock()

        msg, tone_mod = await service.apply_tone_to_message("a", "b", "Hello")

        assert "😒" in msg
        assert "Hello" in msg

    @pytest.mark.asyncio
    async def test_get_all_relationships_delegates_to_repo(self):
        """get_all_relationships forwards to repository."""
        mock_redis = MagicMock()
        service = AgentRelationshipService(mock_redis)

        rels = [AgentRelationship(agent_a="a", agent_b="c")]
        service.repository.get_all_for_agent = AsyncMock(return_value=rels)

        result = await service.get_all_relationships("a")

        assert result == rels
        service.repository.get_all_for_agent.assert_called_once_with("a")

    @pytest.mark.asyncio
    async def test_decay_scores_skips_low_interaction_count(self):
        """decay_scores ignores relationships with fewer than 3 interactions."""
        mock_redis = MagicMock()
        service = AgentRelationshipService(mock_redis)

        rel = AgentRelationship(agent_a="a", agent_b="b", score=50.0, interaction_count=2)
        service.repository.get_all_for_agent = AsyncMock(return_value=[rel])
        service.repository.save = AsyncMock()

        updated = await service.decay_scores()

        assert updated == 0
        service.repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_decay_scores_applies_when_stale(self):
        """decay_scores applies decay for relationships older than 7 days."""
        from datetime import timedelta

        mock_redis = MagicMock()
        service = AgentRelationshipService(mock_redis)

        rel = AgentRelationship(
            agent_a="a",
            agent_b="b",
            score=50.0,
            interaction_count=5,
            last_interaction=datetime.utcnow() - timedelta(days=10),
        )
        service.repository.get_all_for_agent = AsyncMock(return_value=[rel])
        service.repository.save = AsyncMock()

        updated = await service.decay_scores(decay_factor=0.1)

        assert updated == 1
        assert rel.score < 50.0
        service.repository.save.assert_called_once()


class TestRelationshipRepository:
    """Tests for RelationshipRepository async operations."""

    @pytest.fixture
    def mock_redis(self):
        redis = MagicMock()
        redis.get = AsyncMock()
        redis.set = AsyncMock()
        redis.delete = AsyncMock()
        redis.scan = AsyncMock()
        return redis

    @pytest.mark.asyncio
    async def test_repo_get_returns_none_when_missing(self, mock_redis):
        from src.features.home.agent_relationships.repository import RelationshipRepository as Repo

        mock_redis.get.return_value = None
        repo = Repo(mock_redis)
        result = await repo.get("a", "b")
        assert result is None

    @pytest.mark.asyncio
    async def test_repo_get_deserialises_relationship(self, mock_redis):
        from src.features.home.agent_relationships.repository import RelationshipRepository as Repo

        mock_redis.get.return_value = {
            "agent_a": "a",
            "agent_b": "b",
            "score": 10.0,
            "status": "acquaintance",
            "interaction_count": 1,
            "history": [],
        }
        repo = Repo(mock_redis)
        result = await repo.get("a", "b")
        assert result is not None
        assert result.score == 10.0

    @pytest.mark.asyncio
    async def test_repo_save_calls_redis_set(self, mock_redis):
        from src.features.home.agent_relationships.repository import RelationshipRepository as Repo

        repo = Repo(mock_redis)
        rel = AgentRelationship(agent_a="a", agent_b="b")
        await repo.save(rel)
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_repo_delete_calls_redis_delete(self, mock_redis):
        from src.features.home.agent_relationships.repository import RelationshipRepository as Repo

        repo = Repo(mock_redis)
        await repo.delete("a", "b")
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_repo_get_all_for_agent_scans_keys(self, mock_redis):
        from src.features.home.agent_relationships.repository import RelationshipRepository as Repo

        # scan returns (cursor=0, keys=[]) immediately
        mock_redis.scan.return_value = (0, [])
        repo = Repo(mock_redis)
        result = await repo.get_all_for_agent("lisa")
        assert result == []
        mock_redis.scan.assert_called_once()

    @pytest.mark.asyncio
    async def test_repo_get_handles_exception(self, mock_redis):
        from src.features.home.agent_relationships.repository import RelationshipRepository as Repo

        mock_redis.get.side_effect = Exception("redis down")
        repo = Repo(mock_redis)
        result = await repo.get("a", "b")
        assert result is None
