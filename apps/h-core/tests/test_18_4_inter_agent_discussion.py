import asyncio
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch


def _make_arbiter():
    from src.features.home.social_arbiter.arbiter import SocialArbiter
    from src.features.home.social_arbiter.models import AgentProfile

    arbiter = SocialArbiter()

    lisa = AgentProfile(agent_id="lisa", name="Lisa", role="guide", domains=["conversation"])
    renarde = AgentProfile(agent_id="renarde", name="Renarde", role="esprit", domains=["art"])
    arbiter.register_agent(lisa)
    arbiter.register_agent(renarde)
    return arbiter, lisa, renarde


class TestDiscussionInterestDecay:
    @pytest.mark.asyncio
    async def test_determine_responder_async_accepts_discussion_turn(self):
        arbiter, _, _ = _make_arbiter()
        with patch.object(
            arbiter.scoring_engine, "calculate_relevance_llm", new=AsyncMock(return_value={"lisa": 0.9, "renarde": 0.8})
        ):
            result = await arbiter.determine_responder_async("Bonjour", discussion_turn=0)
        assert result is not None

    @pytest.mark.asyncio
    async def test_high_turn_reduces_effective_scores_below_threshold(self):
        arbiter, _, _ = _make_arbiter()
        with patch.object(
            arbiter.scoring_engine,
            "calculate_relevance_llm",
            new=AsyncMock(return_value={"lisa": 0.5, "renarde": 0.5}),
        ):
            result_turn0 = await arbiter.determine_responder_async("Hmm", discussion_turn=0)
            result_turn9 = await arbiter.determine_responder_async("Hmm", discussion_turn=9)

        assert (
            result_turn9 is None
            or result_turn9 == []
            or (result_turn0 is not None and (result_turn9 is None or len(result_turn9) == 0))
        )

    @pytest.mark.asyncio
    async def test_turn0_applies_no_decay(self):
        arbiter, _, _ = _make_arbiter()
        with patch.object(
            arbiter.scoring_engine,
            "calculate_relevance_llm",
            new=AsyncMock(return_value={"lisa": 0.9, "renarde": 0.85}),
        ):
            result = await arbiter.determine_responder_async("Raconte quelque chose", discussion_turn=0)
        assert result is not None
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_decay_factor_is_applied_per_turn(self):
        from src.features.home.social_arbiter.arbiter import SocialArbiter

        arbiter = SocialArbiter()
        assert hasattr(arbiter, "_compute_discussion_decay")
        assert arbiter._compute_discussion_decay(0) == pytest.approx(1.0)
        assert arbiter._compute_discussion_decay(5) == pytest.approx(0.5)
        assert arbiter._compute_discussion_decay(10) >= 0.1

    def test_decay_never_drops_below_minimum(self):
        from src.features.home.social_arbiter.arbiter import SocialArbiter

        arbiter = SocialArbiter()
        for turn in range(20):
            factor = arbiter._compute_discussion_decay(turn)
            assert factor >= 0.1, f"Decay below minimum at turn {turn}: {factor}"


class TestDiscussionBudgetRouting:
    @pytest.mark.asyncio
    async def test_budget_decrements_per_inter_agent_message(self):
        from src.main import HaremOrchestrator

        orch = HaremOrchestrator.__new__(HaremOrchestrator)
        orch.discussion_budget = 5
        orch.MAX_DISCUSSION_BUDGET = 5
        orch.agent_registry = MagicMock()
        orch.agent_registry.agents = {}
        orch.social_arbiter = MagicMock()
        orch.social_arbiter.determine_responder_async = AsyncMock(return_value=None)
        orch.redis = MagicMock()
        orch.redis.publish = AsyncMock()
        orch.surreal = MagicMock()

        data = {
            "type": "narrative.text",
            "sender": {"agent_id": "lisa", "role": "agent"},
            "recipient": {"target": "renarde"},
            "payload": {"content": "Qu'est-ce que tu en penses ?"},
            "id": str(uuid4()),
        }

        await orch.handle_message(data)
        assert orch.discussion_budget == 4

    @pytest.mark.asyncio
    async def test_budget_zero_stops_inter_agent_routing(self):
        from src.main import HaremOrchestrator

        orch = HaremOrchestrator.__new__(HaremOrchestrator)
        orch.discussion_budget = 0
        orch.MAX_DISCUSSION_BUDGET = 5
        orch.agent_registry = MagicMock()
        orch.agent_registry.agents = {}
        orch.social_arbiter = MagicMock()
        orch.social_arbiter.determine_responder_async = AsyncMock(return_value=None)
        orch.redis = MagicMock()
        orch.redis.publish = AsyncMock()
        orch.surreal = MagicMock()

        data = {
            "type": "narrative.text",
            "sender": {"agent_id": "lisa", "role": "agent"},
            "recipient": {"target": "renarde"},
            "payload": {"content": "Et toi ?"},
            "id": str(uuid4()),
        }

        await orch.handle_message(data)
        orch.social_arbiter.determine_responder_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_agent_cannot_respond_to_itself(self):
        from src.main import HaremOrchestrator

        orch = HaremOrchestrator.__new__(HaremOrchestrator)
        orch.discussion_budget = 3
        orch.MAX_DISCUSSION_BUDGET = 5
        orch.agent_registry = MagicMock()
        orch.agent_registry.agents = {}

        lisa_profile = MagicMock()
        lisa_profile.agent_id = "lisa"

        orch.social_arbiter = MagicMock()
        orch.social_arbiter.determine_responder_async = AsyncMock(return_value=[lisa_profile])
        orch.redis = MagicMock()
        orch.redis.publish = AsyncMock()
        orch.surreal = MagicMock()

        data = {
            "type": "narrative.text",
            "sender": {"agent_id": "lisa", "role": "agent"},
            "recipient": {"target": "renarde"},
            "payload": {"content": "Je me parle à moi-même ?"},
            "id": str(uuid4()),
        }

        await orch.handle_message(data)
        orch.redis.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_user_message_resets_budget(self):
        from src.main import HaremOrchestrator

        orch = HaremOrchestrator.__new__(HaremOrchestrator)
        orch.discussion_budget = 1
        orch.MAX_DISCUSSION_BUDGET = 5
        orch.agent_registry = MagicMock()
        orch.agent_registry.agents = {}
        orch.social_arbiter = MagicMock()
        orch.social_arbiter.determine_responder_async = AsyncMock(return_value=None)
        orch.redis = MagicMock()
        orch.redis.publish = AsyncMock()
        orch.surreal = MagicMock()

        data = {
            "type": "user_message",
            "sender": {"agent_id": "user", "role": "user"},
            "recipient": {"target": "broadcast"},
            "payload": {"content": "Nouvelle question !"},
            "id": str(uuid4()),
        }

        await orch.handle_message(data)
        assert orch.discussion_budget == 5

    @pytest.mark.asyncio
    async def test_dynamic_threshold_increases_with_turns(self):
        from src.main import HaremOrchestrator

        orch = HaremOrchestrator.__new__(HaremOrchestrator)
        orch.MAX_DISCUSSION_BUDGET = 5
        orch.agent_registry = MagicMock()
        orch.agent_registry.agents = {}
        orch.redis = MagicMock()
        orch.redis.publish = AsyncMock()
        orch.surreal = MagicMock()

        captured_thresholds = []

        async def capture_threshold(content, min_threshold_override=None, discussion_turn=0, **kwargs):
            captured_thresholds.append(min_threshold_override)
            return None

        orch.social_arbiter = MagicMock()
        orch.social_arbiter.determine_responder_async = AsyncMock(side_effect=capture_threshold)

        for budget in [5, 4, 3]:
            orch.discussion_budget = budget
            data = {
                "type": "narrative.text",
                "sender": {"agent_id": "lisa", "role": "agent"},
                "recipient": {"target": "renarde"},
                "payload": {"content": "Hmm"},
                "id": str(uuid4()),
            }
            await orch.handle_message(data)

        assert len(captured_thresholds) >= 2
        assert captured_thresholds[-1] > captured_thresholds[0], (
            f"Threshold should increase over turns: {captured_thresholds}"
        )
