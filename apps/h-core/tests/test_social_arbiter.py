import pytest
import asyncio
import sys

sys.path.insert(0, "src/features/home")
from social_arbiter.models import AgentProfile
from social_arbiter.scoring import ScoringEngine
from social_arbiter.tiebreaker import Tiebreaker
from social_arbiter.fallback import FallbackBehavior
from social_arbiter.arbiter import SocialArbiter
from social_arbiter.turn_taking import TurnManager, TurnState, TurnTimeoutConfig, QueuedResponse


class TestScoringEngine:
    def test_relevance_domain_match(self):
        engine = ScoringEngine()
        agent = AgentProfile(
            agent_id="test",
            name="Test",
            role="assistant",
            domains=["home", "automation"],
            expertise=["lights", "climate"],
        )

        score = engine._calculate_relevance(agent, "Can you help with home automation and lights?")
        assert score > 0.5

    def test_interest_match(self):
        engine = ScoringEngine()
        agent = AgentProfile(
            agent_id="test",
            name="Test",
            role="assistant",
            interests=["cooking", "music"],
        )

        score = engine._calculate_interest_match(agent, "I love cooking and music")
        assert score > 0.5

    def test_emotional_fit(self):
        engine = ScoringEngine()
        agent = AgentProfile(
            agent_id="test",
            name="Test",
            role="assistant",
            personality_traits=["empathetic", "calm"],
        )

        emotional_context = {
            "required_emotions": ["empathetic"],
            "personality_match": ["calm"],
        }

        score = engine._calculate_emotional_fit(agent, emotional_context)
        assert score >= 0.5

    def test_full_scoring(self):
        engine = ScoringEngine()
        agent = AgentProfile(
            agent_id="test",
            name="Test",
            role="assistant",
            domains=["tech"],
            interests=["ai"],
            personality_traits=["analytical"],
            priority_weight=1.0,
        )

        score = engine.score_agent(agent, "Tell me about AI technology", None)
        assert score > 0

    def test_tie_detection(self):
        engine = ScoringEngine(tiebreaker_margin=0.1)
        assert engine.are_scores_tied(0.8, 0.85) is True
        assert engine.are_scores_tied(0.8, 0.5) is False


class TestTiebreaker:
    def test_single_agent(self):
        tiebreaker = Tiebreaker()
        agents = [(AgentProfile(agent_id="a", name="A", role="test"), 0.8)]
        result = tiebreaker.apply(agents)
        assert len(result) == 1

    def test_tied_scores_sorted_by_response_count(self):
        tiebreaker = Tiebreaker()
        agents = [
            (AgentProfile(agent_id="a", name="A", role="test", response_count=5), 0.8),
            (AgentProfile(agent_id="b", name="B", role="test", response_count=2), 0.8),
        ]
        result = tiebreaker.apply(agents)
        assert result[0][0].agent_id == "b"

    def test_tied_scores_sorted_by_agent_id(self):
        tiebreaker = Tiebreaker()
        agents = [
            (AgentProfile(agent_id="b", name="B", role="test", response_count=0), 0.8),
            (AgentProfile(agent_id="a", name="A", role="test", response_count=0), 0.8),
        ]
        result = tiebreaker.apply(agents)
        assert result[0][0].agent_id == "a"


class TestFallbackBehavior:
    def test_above_threshold_selected(self):
        fallback = FallbackBehavior(minimum_threshold=0.2)
        agents = [
            (AgentProfile(agent_id="a", name="A", role="test", is_active=True), 0.5),
            (AgentProfile(agent_id="b", name="B", role="test", is_active=True), 0.3),
        ]

        result = fallback.select_agent(agents, [a for a, _ in agents])
        assert result.agent_id == "a"

    def test_below_threshold_uses_default(self):
        fallback = FallbackBehavior(
            minimum_threshold=0.5,
            default_agent_id="default",
        )
        all_agents = [
            AgentProfile(agent_id="default", name="Default", role="test", is_active=True),
            AgentProfile(agent_id="a", name="A", role="test", is_active=True),
        ]
        agents = [
            (AgentProfile(agent_id="a", name="A", role="test", is_active=True), 0.3),
        ]

        result = fallback.select_agent(agents, all_agents)
        assert result.agent_id == "default"

    def test_no_agents_returns_none(self):
        fallback = FallbackBehavior()
        result = fallback.select_agent([], [])
        assert result is None


class TestSocialArbiter:
    def test_register_and_list_agents(self):
        arbiter = SocialArbiter()
        agent = AgentProfile(agent_id="test", name="Test", role="assistant")

        arbiter.register_agent(agent)
        agents = arbiter.get_registered_agents()

        assert len(agents) == 1
        assert agents[0].agent_id == "test"

    def test_determine_responder_by_mention(self):
        arbiter = SocialArbiter()
        arbiter.register_agent(AgentProfile(agent_id="lisa", name="Lisa", role="assistant"))
        arbiter.register_agent(AgentProfile(agent_id="renarde", name="Renarde", role="assistant"))

        responder = arbiter.determine_responder(
            "Hello Lisa!",
            mentioned_agents=["lisa"],
        )

        if isinstance(responder, list):
            responder = responder[0]
        assert responder.agent_id == "lisa"

    def test_determine_responder_by_relevance(self):
        arbiter = SocialArbiter()
        arbiter.register_agent(
            AgentProfile(
                agent_id="tech",
                name="Tech",
                role="assistant",
                domains=["technology", "computers"],
            )
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="chef",
                name="Chef",
                role="assistant",
                domains=["cooking", "food"],
            )
        )

        responder = arbiter.determine_responder("Tell me about technology")

        assert isinstance(responder, list) and len(responder) == 1
        assert responder[0].agent_id == "tech"

    def test_determine_responder_fallback(self):
        arbiter = SocialArbiter(minimum_threshold=0.5)
        arbiter.register_agent(
            AgentProfile(
                agent_id="a",
                name="A",
                role="assistant",
                is_active=False,
            )
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="b",
                name="B",
                role="assistant",
                is_active=True,
            )
        )

        responder = arbiter.determine_responder("Hello!", allow_suppression=False)

        if isinstance(responder, list):
            responder = responder[0]
        assert responder.agent_id == "b"

    def test_rank_agents(self):
        arbiter = SocialArbiter()
        arbiter.register_agent(
            AgentProfile(
                agent_id="tech",
                name="Tech",
                role="assistant",
                domains=["technology"],
            )
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="chef",
                name="Chef",
                role="assistant",
                domains=["cooking"],
            )
        )

        rankings = arbiter.rank_agents("Tell me about technology")

        assert len(rankings) == 2
        assert rankings[0][0].agent_id == "tech"
        assert rankings[0][1] >= rankings[1][1]

    def test_update_stats(self):
        arbiter = SocialArbiter()
        arbiter.register_agent(
            AgentProfile(
                agent_id="test",
                name="Test",
                role="assistant",
                response_count=0,
            )
        )

        arbiter.update_agent_stats("test", 1.5)

        agent = arbiter.get_registered_agents()[0]
        assert agent.response_count == 1
        assert agent.last_response_time == 1.5


class TestNameExtractor:
    def test_extract_name_with_comma(self):
        from social_arbiter.name_detection import NameExtractor

        extractor = NameExtractor()

        name = extractor.extract_name_from_message("Lisa, tu peux me dire...")
        assert name == "Lisa"

    def test_extract_name_with_at_sign(self):
        from social_arbiter.name_detection import NameExtractor

        extractor = NameExtractor()

        name = extractor.extract_name_from_message("@Marie dis-moi")
        assert name == "Marie"

    def test_extract_name_with_colon(self):
        from social_arbiter.name_detection import NameExtractor

        extractor = NameExtractor()

        name = extractor.extract_name_from_message("Paul: raconte")
        assert name == "Paul"

    def test_extract_name_with_bonjour(self):
        from social_arbiter.name_detection import NameExtractor

        extractor = NameExtractor()

        name = extractor.extract_name_from_message("Bonjour Lisa")
        assert name == "Lisa"

    def test_extract_name_with_dis(self):
        from social_arbiter.name_detection import NameExtractor

        extractor = NameExtractor()

        name = extractor.extract_name_from_message("Dis Paul")
        assert name == "Paul"

    def test_extract_name_with_hey(self):
        from social_arbiter.name_detection import NameExtractor

        extractor = NameExtractor()

        name = extractor.extract_name_from_message("Hey Marie")
        assert name == "Marie"

    def test_find_agent_by_exact_name(self):
        from social_arbiter.name_detection import NameExtractor

        extractor = NameExtractor()

        agents = {
            "lisa": AgentProfile(agent_id="lisa", name="Lisa", role="assistant", is_active=True),
            "marie": AgentProfile(agent_id="marie", name="Marie", role="assistant", is_active=True),
        }

        agent_id, is_exact = extractor.find_agent_by_name("Lisa", agents)
        assert agent_id == "lisa"
        assert is_exact is True

    def test_find_agent_by_partial_match(self):
        from social_arbiter.name_detection import NameExtractor

        extractor = NameExtractor()

        agents = {
            "lisa": AgentProfile(agent_id="lisa", name="Lisa", role="assistant", is_active=True),
            "marie": AgentProfile(agent_id="marie", name="Marie", role="assistant", is_active=True),
        }

        agent_id, is_exact = extractor.find_agent_by_name("Lis", agents)
        assert agent_id == "lisa"

    def test_find_agent_not_found(self):
        from social_arbiter.name_detection import NameExtractor

        extractor = NameExtractor()

        agents = {
            "lisa": AgentProfile(agent_id="lisa", name="Lisa", role="assistant", is_active=True),
        }

        agent_id, is_exact = extractor.find_agent_by_name("Unknown", agents)
        assert agent_id is None

    def test_find_agent_short_name_filtered(self):
        from social_arbiter.name_detection import NameExtractor

        extractor = NameExtractor()

        agents = {
            "lisa": AgentProfile(agent_id="lisa", name="Lisa", role="assistant", is_active=True),
        }

        agent_id, is_exact = extractor.find_agent_by_name("Li", agents)
        assert agent_id is None


class TestNamedAgentPriority:
    def test_named_agent_priority_explicit_name(self):
        arbiter = SocialArbiter()
        arbiter.register_agent(
            AgentProfile(
                agent_id="lisa",
                name="Lisa",
                role="assistant",
                domains=["general"],
                is_active=True,
            )
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="marie",
                name="Marie",
                role="assistant",
                domains=["general"],
                is_active=True,
            )
        )

        responder = arbiter.determine_responder("Lisa, comment ça va?")

        if isinstance(responder, list):
            responder = responder[0]
        assert responder.agent_id == "lisa"

    def test_named_agent_priority_at_mention(self):
        arbiter = SocialArbiter()
        arbiter.register_agent(
            AgentProfile(
                agent_id="lisa",
                name="Lisa",
                role="assistant",
                domains=["general"],
                is_active=True,
            )
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="marie",
                name="Marie",
                role="assistant",
                domains=["general"],
                is_active=True,
            )
        )

        responder = arbiter.determine_responder("@Marie dis-moi quelque chose")

        if isinstance(responder, list):
            responder = responder[0]
        assert responder.agent_id == "marie"

    def test_named_agent_priority_bonjour(self):
        arbiter = SocialArbiter()
        arbiter.register_agent(
            AgentProfile(
                agent_id="lisa",
                name="Lisa",
                role="assistant",
                domains=["general"],
                is_active=True,
            )
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="marie",
                name="Marie",
                role="assistant",
                domains=["general"],
                is_active=True,
            )
        )

        responder = arbiter.determine_responder("Bonjour Lisa")

        if isinstance(responder, list):
            responder = responder[0]
        assert responder.agent_id == "lisa"

    def test_unknown_agent_fallback_to_scoring(self):
        arbiter = SocialArbiter()
        arbiter.register_agent(
            AgentProfile(
                agent_id="lisa",
                name="Lisa",
                role="assistant",
                domains=["general"],
                is_active=True,
            )
        )

        responder = arbiter.determine_responder("John, dis bonjour", allow_suppression=False)

        if isinstance(responder, list):
            responder = responder[0]
        assert responder.agent_id == "lisa"

    def test_no_name_uses_scoring(self):
        arbiter = SocialArbiter()
        arbiter.register_agent(
            AgentProfile(
                agent_id="tech",
                name="Tech",
                role="assistant",
                domains=["technology"],
                is_active=True,
            )
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="chef",
                name="Chef",
                role="assistant",
                domains=["cooking"],
                is_active=True,
            )
        )

        responder = arbiter.determine_responder("Tell me about technology")

        assert responder.agent_id == "tech"

    def test_named_agent_inactive_not_selected(self):
        arbiter = SocialArbiter()
        arbiter.register_agent(
            AgentProfile(
                agent_id="lisa",
                name="Lisa",
                role="assistant",
                domains=["general"],
                is_active=False,
            )
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="marie",
                name="Marie",
                role="assistant",
                domains=["general"],
                is_active=True,
            )
        )

        responder = arbiter.determine_responder("Lisa, dis-moi quelque chose", allow_suppression=False)

        if isinstance(responder, list):
            responder = responder[0]
        assert responder.agent_id == "marie"


class TestTurnManager:
    @pytest.mark.asyncio
    async def test_request_turn_idle_state(self):
        manager = TurnManager()
        result = await manager.request_turn("agent1", "Hello")

        assert result is True
        assert manager.state == TurnState.RESPONDING
        assert manager.current_agent == "agent1"

    @pytest.mark.asyncio
    async def test_request_turn_while_responding_queues(self):
        manager = TurnManager()
        await manager.request_turn("agent1", "Hello")

        result = await manager.request_turn("agent2", "World")

        assert result is False
        assert manager.state == TurnState.QUEUED
        assert manager.queue_size == 1
        assert manager.current_agent == "agent1"

    @pytest.mark.asyncio
    async def test_request_turn_same_agent_returns_true(self):
        manager = TurnManager()
        await manager.request_turn("agent1", "Hello")

        result = await manager.request_turn("agent1", "World")

        assert result is True
        assert manager.current_agent == "agent1"

    @pytest.mark.asyncio
    async def test_state_transition_idle_to_responding_to_queued(self):
        manager = TurnManager()

        assert manager.state == TurnState.IDLE

        await manager.request_turn("agent1", "Hello")
        assert manager.state == TurnState.RESPONDING

        await manager.request_turn("agent2", "World")
        assert manager.state == TurnState.QUEUED

    @pytest.mark.asyncio
    async def test_state_transition_queued_to_responding_on_release(self):
        manager = TurnManager()
        await manager.request_turn("agent1", "Hello")
        await manager.request_turn("agent2", "World")

        assert manager.queue_size == 1

        await manager.release_turn()

        assert manager.state == TurnState.RESPONDING
        assert manager.current_agent == "agent2"
        assert manager.queue_size == 0

    @pytest.mark.asyncio
    async def test_state_transition_to_idle_when_queue_empty(self):
        manager = TurnManager()
        await manager.request_turn("agent1", "Hello")

        await manager.release_turn()

        assert manager.state == TurnState.IDLE
        assert manager.current_agent is None


class TestTurnManagerMultipleAgents:
    @pytest.mark.asyncio
    async def test_multiple_agents_request_turn_simultaneously(self):
        manager = TurnManager()

        result1 = await manager.request_turn("agent1", "Hello")
        result2 = await manager.request_turn("agent2", "World")
        result3 = await manager.request_turn("agent3", "Test")

        assert result1 is True
        assert result2 is False
        assert result3 is False

        assert manager.current_agent == "agent1"
        assert manager.queue_size == 2

        queued_agents = [q.agent_id for q in manager._response_queue]
        assert queued_agents == ["agent2", "agent3"]

    @pytest.mark.asyncio
    async def test_concurrent_request_turn_order(self):
        manager = TurnManager()

        await manager.request_turn("agent1", "First")
        await manager.request_turn("agent2", "Second")
        await manager.request_turn("agent3", "Third")

        assert manager.queue_size == 2
        assert manager._response_queue[0].agent_id == "agent2"
        assert manager._response_queue[1].agent_id == "agent3"


class TestTurnManagerTimeout:
    @pytest.mark.asyncio
    async def test_timeout_releases_turn(self):
        config = TurnTimeoutConfig(default_timeout=0.1)
        manager = TurnManager(timeout_config=config)
        callback_called = False

        async def callback():
            nonlocal callback_called
            callback_called = True

        manager.set_timeout_callback(callback)
        await manager.request_turn("agent1", "Hello")

        await asyncio.sleep(0.2)

        assert manager.state == TurnState.IDLE
        assert callback_called is True

    @pytest.mark.asyncio
    async def test_timeout_callback_on_timeout(self):
        config = TurnTimeoutConfig(default_timeout=0.1)
        manager = TurnManager(timeout_config=config)
        callback_result = []

        async def callback():
            callback_result.append("called")

        manager.set_timeout_callback(callback)
        await manager.request_turn("agent1", "Hello")

        await asyncio.sleep(0.2)

        assert callback_result == ["called"]

    @pytest.mark.asyncio
    async def test_timeout_transfers_to_next_in_queue(self):
        config = TurnTimeoutConfig(default_timeout=0.1)
        manager = TurnManager(timeout_config=config)

        await manager.request_turn("agent1", "Hello")
        await manager.request_turn("agent2", "World")

        assert manager.current_agent == "agent1"
        assert manager.queue_size == 1
        assert manager.state == TurnState.QUEUED

        await manager.release_turn()

        assert manager.state == TurnState.RESPONDING
        assert manager.current_agent == "agent2"
        assert manager.queue_size == 0


class TestTurnManagerQueue:
    @pytest.mark.asyncio
    async def test_queue_priority_sorting(self):
        manager = TurnManager()

        await manager.request_turn("agent1", "Low priority")
        await manager.request_turn("agent2", "High priority", metadata={"priority": 10})
        await manager.request_turn("agent3", "Medium priority", metadata={"priority": 5})

        assert manager.queue_size == 2
        assert manager._response_queue[0].agent_id == "agent2"
        assert manager._response_queue[1].agent_id == "agent3"

    @pytest.mark.asyncio
    async def test_queue_cancel_current_agent(self):
        manager = TurnManager()
        await manager.request_turn("agent1", "Hello")
        await manager.request_turn("agent2", "World")

        result = await manager.cancel_turn("agent1")

        assert result is True
        assert manager.current_agent == "agent2"
        assert manager.queue_size == 0
        assert manager.state == TurnState.RESPONDING

    @pytest.mark.asyncio
    async def test_queue_cancel_queued_agent(self):
        manager = TurnManager()
        await manager.request_turn("agent1", "Hello")
        await manager.request_turn("agent2", "World")
        await manager.request_turn("agent3", "Test")

        result = await manager.cancel_turn("agent2")

        assert result is True
        assert manager.queue_size == 1
        assert manager._response_queue[0].agent_id == "agent3"

    @pytest.mark.asyncio
    async def test_queue_cancel_nonexistent_agent(self):
        manager = TurnManager()
        await manager.request_turn("agent1", "Hello")

        result = await manager.cancel_turn("nonexistent")

        assert result is False
        assert manager.queue_size == 0

    @pytest.mark.asyncio
    async def test_queue_timeout_warning_threshold(self):
        config = TurnTimeoutConfig(default_timeout=10.0, warning_threshold=0.5)
        manager = TurnManager(timeout_config=config)

        await manager.request_turn("agent1", "Hello")

        status = await manager.get_queue_status()

        assert status["timeout_warning"] is False

        import time

        manager._turn_start_time = time.time() - 6.0

        status = await manager.get_queue_status()

        assert status["timeout_warning"] is True

    @pytest.mark.asyncio
    async def test_clear_queue(self):
        manager = TurnManager()
        await manager.request_turn("agent1", "Hello")
        await manager.request_turn("agent2", "World")
        await manager.request_turn("agent3", "Test")

        cleared = await manager.clear_queue()

        assert cleared == 2
        assert manager.queue_size == 0

    @pytest.mark.asyncio
    async def test_get_queue_status(self):
        manager = TurnManager()
        await manager.request_turn("agent1", "Hello")
        await manager.request_turn("agent2", "World")

        status = await manager.get_queue_status()

        assert status["state"] == "queued"
        assert status["current_agent"] == "agent1"
        assert status["queue_size"] == 1
        assert status["queued_agents"] == ["agent2"]

    @pytest.mark.asyncio
    async def test_force_state_idle_clears_queue(self):
        manager = TurnManager()
        await manager.request_turn("agent1", "Hello")
        await manager.request_turn("agent2", "World")

        await manager.force_state(TurnState.IDLE)

        assert manager.state == TurnState.IDLE
        assert manager.queue_size == 0
        assert manager.current_agent is None


class TestTurnManagerSetTimeout:
    @pytest.mark.asyncio
    async def test_set_timeout_within_bounds(self):
        manager = TurnManager()

        manager.set_timeout(60.0)

        assert manager.timeout_config.default_timeout == 60.0

    @pytest.mark.asyncio
    async def test_set_timeout_clamped_to_min(self):
        manager = TurnManager()

        manager.set_timeout(1.0)

        assert manager.timeout_config.default_timeout == 5.0

    @pytest.mark.asyncio
    async def test_set_timeout_clamped_to_max(self):
        manager = TurnManager()

        manager.set_timeout(200.0)

        assert manager.timeout_config.default_timeout == 120.0


class TestQueuedResponse:
    def test_queued_response_priority_sorting(self):
        r1 = QueuedResponse("a", "msg", 1.0, priority=5)
        r2 = QueuedResponse("b", "msg", 2.0, priority=10)
        r3 = QueuedResponse("c", "msg", 3.0, priority=5)

        queue = [r1, r2, r3]
        queue.sort()

        assert queue[0].agent_id == "b"
        assert queue[1].agent_id == "a"
        assert queue[2].agent_id == "c"

    def test_queued_response_timestamp_sorting(self):
        r1 = QueuedResponse("a", "msg", 1.0, priority=5)
        r2 = QueuedResponse("b", "msg", 2.0, priority=5)
        r3 = QueuedResponse("c", "msg", 3.0, priority=5)

        queue = [r3, r1, r2]
        queue.sort()

        assert queue[0].agent_id == "a"
        assert queue[1].agent_id == "b"
        assert queue[2].agent_id == "c"


class TestResponseSuppressor:
    def test_suppress_below_threshold(self):
        from social_arbiter.suppression import ResponseSuppressor, SuppressionConfig, SuppressionReason

        config = SuppressionConfig(minimum_threshold=0.3)
        suppressor = ResponseSuppressor(config)

        result = suppressor.suppress_response(
            agent_id="agent1",
            message_content="Hello",
            score=0.2,
            reason=SuppressionReason.BELOW_THRESHOLD,
        )

        assert result is not None
        assert result.agent_id == "agent1"
        assert result.score == 0.2

    def test_no_suppress_above_threshold(self):
        from social_arbiter.suppression import ResponseSuppressor, SuppressionConfig

        config = SuppressionConfig(minimum_threshold=0.3)
        suppressor = ResponseSuppressor(config)

        result = suppressor.suppress_response(
            agent_id="agent1",
            message_content="Hello",
            score=0.5,
        )

        assert result is None

    def test_suppression_disabled(self):
        from social_arbiter.suppression import ResponseSuppressor, SuppressionConfig

        config = SuppressionConfig(enable_suppression=False)
        suppressor = ResponseSuppressor(config)

        result = suppressor.suppress_response(
            agent_id="agent1",
            message_content="Hello",
            score=0.1,
        )

        assert result is None

    def test_suppression_queue(self):
        from social_arbiter.suppression import ResponseSuppressor, SuppressionConfig, SuppressionReason

        config = SuppressionConfig(
            minimum_threshold=0.3,
            enable_reevaluation=True,
            reevaluation_delay_seconds=0,
        )
        suppressor = ResponseSuppressor(config)

        suppressor.suppress_response(
            agent_id="agent1",
            message_content="Hello",
            score=0.2,
            reason=SuppressionReason.BELOW_THRESHOLD,
        )

        assert suppressor.get_queue_size() == 1

    def test_suppression_stats(self):
        from social_arbiter.suppression import ResponseSuppressor, SuppressionConfig, SuppressionReason

        config = SuppressionConfig(minimum_threshold=0.3)
        suppressor = ResponseSuppressor(config)

        suppressor.suppress_response(
            agent_id="agent1",
            message_content="Hello",
            score=0.2,
            reason=SuppressionReason.BELOW_THRESHOLD,
        )

        stats = suppressor.get_stats()

        assert stats["total_suppressions"] == 1
        assert stats["by_agent"]["agent1"] == 1

    def test_suppression_logging(self):
        from social_arbiter.suppression import ResponseSuppressor, SuppressionConfig, SuppressionReason

        config = SuppressionConfig(minimum_threshold=0.3)
        suppressor = ResponseSuppressor(config)

        suppressor.suppress_response(
            agent_id="agent1",
            message_content="Test message for logging",
            score=0.2,
            reason=SuppressionReason.LOW_RELEVANCE_SCORE,
        )

        history = suppressor.suppression_logger.get_suppression_history()

        assert len(history) == 1
        assert history[0]["agent_id"] == "agent1"
        assert history[0]["reason"] == "low_relevance_score"


class TestSocialArbiterSuppression:
    def test_determine_responder_suppresses_low_score(self):
        arbiter = SocialArbiter(
            suppression_config={
                "minimum_threshold": 0.3,
                "enable_suppression": True,
            }
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="tech",
                name="Tech",
                role="assistant",
                domains=["tech"],
            )
        )

        responder = arbiter.determine_responder("Hello world")

        assert responder is None
        stats = arbiter.get_suppression_stats()
        assert stats["total_suppressions"] >= 1

    def test_determine_responder_allows_high_score(self):
        arbiter = SocialArbiter(
            suppression_config={
                "minimum_threshold": 0.1,
                "enable_suppression": True,
            }
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="tech",
                name="Tech",
                role="assistant",
                domains=["technology"],
            )
        )

        responder = arbiter.determine_responder("Tell me about technology")

        assert responder is not None
        if isinstance(responder, list):
            responder = responder[0]
        assert responder.agent_id == "tech"

    def test_determine_responder_no_suppression_when_disabled(self):
        arbiter = SocialArbiter(
            suppression_config={
                "minimum_threshold": 0.9,
                "enable_suppression": False,
            }
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="tech",
                name="Tech",
                role="assistant",
                domains=["tech"],
            )
        )

        responder = arbiter.determine_responder("Hello")

        assert responder is not None

    def test_get_suppression_stats(self):
        arbiter = SocialArbiter(suppression_config={"minimum_threshold": 0.3})
        arbiter.register_agent(
            AgentProfile(
                agent_id="tech",
                name="Tech",
                role="assistant",
                domains=["tech"],
            )
        )

        arbiter.determine_responder("Hello")

        stats = arbiter.get_suppression_stats()

        assert "total_suppressions" in stats
        assert "by_agent" in stats
        assert "by_reason" in stats

    def test_get_suppression_history(self):
        arbiter = SocialArbiter(suppression_config={"minimum_threshold": 0.3})
        arbiter.register_agent(
            AgentProfile(
                agent_id="tech",
                name="Tech",
                role="assistant",
                domains=["tech"],
            )
        )

        arbiter.determine_responder("Hello")

        history = arbiter.get_suppression_history()

        assert len(history) >= 1
        assert "agent_id" in history[0]
        assert "score" in history[0]
        assert "reason" in history[0]

    def test_reevaluation_pending_count(self):
        arbiter = SocialArbiter(
            suppression_config={
                "minimum_threshold": 0.3,
                "enable_reevaluation": True,
            }
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="tech",
                name="Tech",
                role="assistant",
                domains=["tech"],
            )
        )

        arbiter.determine_responder("Hello")

        assert arbiter.get_pending_reevaluation_count() >= 1

    def test_clear_suppression_queue(self):
        arbiter = SocialArbiter(
            suppression_config={
                "minimum_threshold": 0.3,
                "enable_reevaluation": True,
            }
        )
        arbiter.register_agent(
            AgentProfile(
                agent_id="tech",
                name="Tech",
                role="assistant",
                domains=["tech"],
            )
        )

        arbiter.determine_responder("Hello")

        cleared = arbiter.clear_suppression_queue()

        assert cleared >= 1
        assert arbiter.get_pending_reevaluation_count() == 0

    def test_set_suppression_threshold(self):
        arbiter = SocialArbiter(suppression_config={"minimum_threshold": 0.3})

        arbiter.set_suppression_threshold(0.5)

        assert arbiter.suppressor.config.minimum_threshold == 0.5

    def test_enable_suppression(self):
        arbiter = SocialArbiter(suppression_config={"minimum_threshold": 0.3})

        arbiter.enable_suppression(False)

        assert arbiter.suppressor.config.enable_suppression is False
