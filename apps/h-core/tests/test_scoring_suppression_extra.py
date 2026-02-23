import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.features.home.social_arbiter.scoring import ScoringEngine
from src.features.home.social_arbiter.suppression import (
    ResponseSuppressor,
    SuppressionConfig,
    SuppressionLogger,
    SuppressedResponse,
    SuppressionReason,
)
from src.features.home.social_arbiter.models import AgentProfile


def make_profile(agent_id="lisa", domains=None, role="assistant", personality_traits=None):
    return AgentProfile(
        agent_id=agent_id,
        name=agent_id.title(),
        role=role,
        domains=domains or ["home", "cooking"],
        expertise=[],
        interests=[],
        personality_traits=personality_traits or [],
        priority_weight=1.0,
    )


class TestScoringEngineLLMPath:
    @pytest.mark.asyncio
    async def test_calculate_relevance_llm_no_llm_client_falls_back_to_rule_based(self):
        engine = ScoringEngine()
        profiles = [make_profile("lisa", domains=["cooking"])]
        scores = await engine.calculate_relevance_llm("I want to cook pasta", profiles)
        assert "lisa" in scores
        assert 0.0 <= scores["lisa"] <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_relevance_llm_with_llm_returns_parsed_scores(self):
        mock_llm = MagicMock()
        mock_llm.get_completion = AsyncMock(return_value='{"lisa": 0.9}')
        engine = ScoringEngine(llm_client=mock_llm)
        profiles = [make_profile("lisa")]
        scores = await engine.calculate_relevance_llm("cook something", profiles)
        assert scores["lisa"] == pytest.approx(0.9)

    @pytest.mark.asyncio
    async def test_calculate_relevance_llm_handles_markdown_code_block(self):
        mock_llm = MagicMock()
        mock_llm.get_completion = AsyncMock(return_value='```json\n{"lisa": 0.8}\n```')
        engine = ScoringEngine(llm_client=mock_llm)
        profiles = [make_profile("lisa")]
        scores = await engine.calculate_relevance_llm("something", profiles)
        assert scores["lisa"] == pytest.approx(0.8)

    @pytest.mark.asyncio
    async def test_calculate_relevance_llm_handles_plain_code_block(self):
        mock_llm = MagicMock()
        mock_llm.get_completion = AsyncMock(return_value='```\n{"lisa": 0.7}\n```')
        engine = ScoringEngine(llm_client=mock_llm)
        profiles = [make_profile("lisa")]
        scores = await engine.calculate_relevance_llm("something", profiles)
        assert scores["lisa"] == pytest.approx(0.7)

    @pytest.mark.asyncio
    async def test_calculate_relevance_llm_falls_back_on_json_error(self):
        mock_llm = MagicMock()
        mock_llm.get_completion = AsyncMock(return_value="not valid json")
        engine = ScoringEngine(llm_client=mock_llm)
        profiles = [make_profile("lisa", domains=["cooking"])]
        scores = await engine.calculate_relevance_llm("cook pasta", profiles)
        assert "lisa" in scores

    @pytest.mark.asyncio
    async def test_calculate_relevance_llm_falls_back_on_llm_exception(self):
        mock_llm = MagicMock()
        mock_llm.get_completion = AsyncMock(side_effect=Exception("timeout"))
        engine = ScoringEngine(llm_client=mock_llm)
        profiles = [make_profile("lisa")]
        scores = await engine.calculate_relevance_llm("something", profiles)
        assert "lisa" in scores

    @pytest.mark.asyncio
    async def test_calculate_relevance_llm_with_emotional_context(self):
        mock_llm = MagicMock()
        mock_llm.get_completion = AsyncMock(return_value='{"lisa": 0.85}')
        engine = ScoringEngine(llm_client=mock_llm)
        profiles = [make_profile("lisa")]
        emotional_context = {"primary_emotion": "happy"}
        scores = await engine.calculate_relevance_llm("great day!", profiles, emotional_context)
        assert scores["lisa"] == pytest.approx(0.85)

    @pytest.mark.asyncio
    async def test_calculate_relevance_llm_missing_agent_gets_default_score(self):
        mock_llm = MagicMock()
        mock_llm.get_completion = AsyncMock(return_value='{"other_agent": 0.9}')
        engine = ScoringEngine(llm_client=mock_llm)
        profiles = [make_profile("lisa")]
        scores = await engine.calculate_relevance_llm("something", profiles)
        assert scores["lisa"] == pytest.approx(0.1)

    @pytest.mark.asyncio
    async def test_calculate_relevance_llm_strips_trailing_comma(self):
        mock_llm = MagicMock()
        mock_llm.get_completion = AsyncMock(return_value='{"lisa": 0.9, }')
        engine = ScoringEngine(llm_client=mock_llm)
        profiles = [make_profile("lisa")]
        scores = await engine.calculate_relevance_llm("something", profiles)
        assert scores["lisa"] == pytest.approx(0.9)

    def test_compute_total_score_aggregates_weights(self):
        engine = ScoringEngine()
        score = engine.compute_total_score(
            text="cook pasta at home",
            domains=["cooking", "home"],
            role="chef",
            time_since_spoke=300.0,
            emotion="neutral",
            personality="neutral",
        )
        assert 0.0 <= score <= 1.0

    def test_apply_repetition_penalty_zero_time(self):
        engine = ScoringEngine()
        penalized = engine.apply_repetition_penalty(1.0, 0.0)
        assert penalized == pytest.approx(0.0)

    def test_apply_repetition_penalty_large_time(self):
        engine = ScoringEngine()
        penalized = engine.apply_repetition_penalty(1.0, 600.0)
        assert penalized > 0.9

    def test_apply_repetition_penalty_negative_time_treated_as_zero(self):
        engine = ScoringEngine()
        penalized = engine.apply_repetition_penalty(1.0, -10.0)
        assert penalized == pytest.approx(0.0)


class TestSuppressionExtra:
    def test_suppressed_response_can_reevaluate_true(self):
        config = SuppressionConfig(enable_reevaluation=True, max_reevaluation_attempts=3)
        sr = SuppressedResponse(
            agent_id="lisa", message_content="hello", score=0.1, reason=SuppressionReason.BELOW_THRESHOLD
        )
        assert sr.can_reevaluate(config) is True

    def test_suppressed_response_can_reevaluate_false_disabled(self):
        config = SuppressionConfig(enable_reevaluation=False)
        sr = SuppressedResponse(
            agent_id="lisa", message_content="hello", score=0.1, reason=SuppressionReason.BELOW_THRESHOLD
        )
        assert sr.can_reevaluate(config) is False

    def test_suppressed_response_can_reevaluate_false_max_reached(self):
        config = SuppressionConfig(max_reevaluation_attempts=2)
        sr = SuppressedResponse(
            agent_id="lisa",
            message_content="hello",
            score=0.1,
            reason=SuppressionReason.BELOW_THRESHOLD,
            reevaluation_count=2,
        )
        assert sr.can_reevaluate(config) is False

    def test_suppressed_response_should_reevaluate_after_delay(self):
        config = SuppressionConfig(reevaluation_delay_seconds=0.0)
        sr = SuppressedResponse(
            agent_id="lisa",
            message_content="hello",
            score=0.1,
            reason=SuppressionReason.BELOW_THRESHOLD,
            timestamp=datetime.now() - timedelta(seconds=1),
        )
        assert sr.should_reevaluate(config) is True

    def test_suppression_logger_clear_history(self):
        sl = SuppressionLogger()
        sr = SuppressedResponse(
            agent_id="lisa", message_content="hello", score=0.1, reason=SuppressionReason.BELOW_THRESHOLD
        )
        sl.log_suppression(sr)
        assert sl.get_suppression_stats()["total_suppressions"] == 1
        sl.clear_history()
        assert sl.get_suppression_stats()["total_suppressions"] == 0

    def test_suppression_logger_get_history(self):
        sl = SuppressionLogger()
        sr = SuppressedResponse(
            agent_id="lisa",
            message_content="hi there something",
            score=0.05,
            reason=SuppressionReason.LOW_RELEVANCE_SCORE,
        )
        sl.log_suppression(sr)
        history = sl.get_suppression_history()
        assert len(history) == 1
        assert history[0]["agent_id"] == "lisa"
        assert history[0]["reason"] == "low_relevance_score"

    def test_response_suppressor_record_and_get_time(self):
        suppressor = ResponseSuppressor()
        suppressor.record_speech("lisa")
        elapsed = suppressor.get_time_since_last_spoke("lisa")
        assert elapsed < 5.0

    def test_response_suppressor_unknown_agent_returns_large_time(self):
        suppressor = ResponseSuppressor()
        elapsed = suppressor.get_time_since_last_spoke("unknown_agent")
        assert elapsed == pytest.approx(999999.0)

    def test_response_suppressor_check_context_change_emotion_changed(self):
        suppressor = ResponseSuppressor()
        sr = SuppressedResponse(
            agent_id="lisa",
            message_content="hello",
            score=0.1,
            reason=SuppressionReason.BELOW_THRESHOLD,
            metadata={"context": {"emotional_context": {"primary_emotion": "sad"}}},
        )
        change = suppressor.check_context_change(sr, {"emotional_context": {"primary_emotion": "happy"}})
        assert change > 0.0

    def test_response_suppressor_check_context_change_no_prior_context(self):
        suppressor = ResponseSuppressor()
        sr = SuppressedResponse(
            agent_id="lisa", message_content="hello", score=0.1, reason=SuppressionReason.BELOW_THRESHOLD, metadata={}
        )
        change = suppressor.check_context_change(sr, {"emotional_context": {"primary_emotion": "happy"}})
        assert change == 0.0

    def test_response_suppressor_check_context_change_mentioned_agents_changed(self):
        suppressor = ResponseSuppressor()
        sr = SuppressedResponse(
            agent_id="lisa",
            message_content="hello",
            score=0.1,
            reason=SuppressionReason.BELOW_THRESHOLD,
            metadata={"context": {"mentioned_agents": ["lisa"]}},
        )
        change = suppressor.check_context_change(sr, {"mentioned_agents": ["electra"]})
        assert change > 0.0

    def test_response_suppressor_get_pending_reevaluations_returns_ready_items(self):
        config = SuppressionConfig(reevaluation_delay_seconds=0.0)
        suppressor = ResponseSuppressor(config=config)
        suppressor._delayed_queue.append(
            SuppressedResponse(
                agent_id="lisa",
                message_content="hello",
                score=0.1,
                reason=SuppressionReason.BELOW_THRESHOLD,
                timestamp=datetime.now() - timedelta(seconds=1),
            )
        )
        pending = suppressor.get_pending_reevaluations()
        assert len(pending) == 1
        assert pending[0].reevaluation_count == 1

    def test_response_suppressor_get_stats_includes_queue_size(self):
        suppressor = ResponseSuppressor()
        stats = suppressor.get_stats()
        assert "delayed_queue_size" in stats
        assert stats["delayed_queue_size"] == 0
