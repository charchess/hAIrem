import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


class TestMetricsCollector:
    def test_metrics_collector_exists(self):
        from src.services.metrics import MetricsCollector

        m = MetricsCollector()
        assert m is not None

    def test_increment_counter(self):
        from src.services.metrics import MetricsCollector

        m = MetricsCollector()
        m.increment("messages_processed")
        assert m.get("messages_processed") == 1

    def test_increment_multiple_times(self):
        from src.services.metrics import MetricsCollector

        m = MetricsCollector()
        m.increment("llm_calls", 3)
        assert m.get("llm_calls") == 3

    def test_observe_histogram(self):
        from src.services.metrics import MetricsCollector

        m = MetricsCollector()
        m.observe("tts_latency_seconds", 0.4)
        m.observe("tts_latency_seconds", 0.8)
        assert m.get_avg("tts_latency_seconds") == pytest.approx(0.6)

    def test_prometheus_text_format(self):
        from src.services.metrics import MetricsCollector

        m = MetricsCollector()
        m.increment("messages_processed", 5)
        text = m.to_prometheus_text()
        assert "messages_processed 5" in text

    def test_prometheus_text_includes_histogram(self):
        from src.services.metrics import MetricsCollector

        m = MetricsCollector()
        m.observe("tts_latency_seconds", 0.5)
        text = m.to_prometheus_text()
        assert "tts_latency_seconds" in text

    def test_global_metrics_singleton(self):
        from src.services.metrics import get_metrics

        a = get_metrics()
        b = get_metrics()
        assert a is b


# 23.2 — agent.speaking signal in generate_response
# ---------------------------------------------------------------------------


class TestAgentSpeakingSignal:
    @pytest.mark.asyncio
    async def test_agent_speaking_published_before_response(self):
        from src.domain.agent import BaseAgent
        from src.models.agent import AgentConfig
        from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

        redis = MagicMock()
        redis.publish = AsyncMock()
        redis.publish_event = AsyncMock()

        llm = MagicMock()
        response_mock = MagicMock()
        response_mock.choices = [MagicMock()]
        response_mock.choices[0].message.content = "Bonjour!"
        llm.get_completion = AsyncMock(return_value=response_mock)
        llm.get_usage_from_response = MagicMock(
            return_value={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
        )
        llm.get_model_provider = MagicMock(return_value=("openai", "gpt-4"))

        config = AgentConfig(name="lisa", role="guide")
        agent = BaseAgent(config, redis, llm)

        msg = HLinkMessage(
            type=MessageType.USER_MESSAGE,
            sender=Sender(agent_id="user", role="user"),
            recipient=Recipient(target="lisa"),
            payload=Payload(content="Bonjour"),
        )

        await agent.generate_response(msg)

        all_calls = redis.publish_event.call_args_list
        speaking_calls = [
            c
            for c in all_calls
            if c[0][0] == "system_stream" and isinstance(c[0][1], dict) and c[0][1].get("type") == "agent.speaking"
        ]
        assert len(speaking_calls) >= 1

    @pytest.mark.asyncio
    async def test_agent_speaking_contains_agent_id(self):
        from src.domain.agent import BaseAgent
        from src.models.agent import AgentConfig
        from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

        redis = MagicMock()
        redis.publish = AsyncMock()
        redis.publish_event = AsyncMock()

        llm = MagicMock()
        response_mock = MagicMock()
        response_mock.choices = [MagicMock()]
        response_mock.choices[0].message.content = "Salut!"
        llm.get_completion = AsyncMock(return_value=response_mock)
        llm.get_usage_from_response = MagicMock(
            return_value={"input_tokens": 5, "output_tokens": 5, "total_tokens": 10}
        )
        llm.get_model_provider = MagicMock(return_value=("openai", "gpt-4"))

        config = AgentConfig(name="renarde", role="esprit")
        agent = BaseAgent(config, redis, llm)

        msg = HLinkMessage(
            type=MessageType.USER_MESSAGE,
            sender=Sender(agent_id="user", role="user"),
            recipient=Recipient(target="renarde"),
            payload=Payload(content="Bonjour"),
        )

        await agent.generate_response(msg)

        all_calls = redis.publish_event.call_args_list
        speaking_calls = [
            c
            for c in all_calls
            if c[0][0] == "system_stream" and isinstance(c[0][1], dict) and c[0][1].get("type") == "agent.speaking"
        ]
        assert any(c[0][1].get("sender", {}).get("agent_id") == "renarde" for c in speaking_calls)


class TestRedisLogHandlerAsyncSafe:
    def test_redis_log_handler_does_not_crash_outside_event_loop(self):
        from src.main import RedisLogHandler

        redis = MagicMock()
        redis.publish_event = AsyncMock()

        handler = RedisLogHandler(redis)
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0, msg="hello log", args=(), exc_info=None
        )
        try:
            handler.emit(record)
        except Exception as e:
            pytest.fail(f"RedisLogHandler.emit raised outside event loop: {e}")

    def test_redis_log_handler_queues_log_in_running_loop(self):
        from src.main import RedisLogHandler

        redis = MagicMock()
        redis.publish_event = AsyncMock()

        handler = RedisLogHandler(redis)
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="", lineno=0, msg="async log", args=(), exc_info=None
        )

        async def _run():
            handler.emit(record)
            await asyncio.sleep(0)

        asyncio.run(_run())


class TestSpeechQueueInterrupt:
    @pytest.mark.asyncio
    async def test_interrupt_clears_queue(self):
        from src.services.audio.speech_queue import SpeechQueue, SpeechRequest

        q = SpeechQueue()
        await q.enqueue(SpeechRequest(text="hello", agent_id="lisa", priority=1))
        await q.enqueue(SpeechRequest(text="world", agent_id="lisa", priority=1))
        assert q.qsize() == 2

        q.interrupt()
        assert q.qsize() == 0

    @pytest.mark.asyncio
    async def test_interrupt_sets_interrupted_flag(self):
        from src.services.audio.speech_queue import SpeechQueue, SpeechRequest

        q = SpeechQueue()
        await q.enqueue(SpeechRequest(text="hello", agent_id="lisa", priority=1))

        q.interrupt()
        assert q.is_interrupted is True

    @pytest.mark.asyncio
    async def test_interrupt_flag_resets_on_next_enqueue(self):
        from src.services.audio.speech_queue import SpeechQueue, SpeechRequest

        q = SpeechQueue()
        q.interrupt()
        assert q.is_interrupted is True

        await q.enqueue(SpeechRequest(text="new item", agent_id="lisa", priority=1))
        assert q.is_interrupted is False

    @pytest.mark.asyncio
    async def test_interrupt_on_empty_queue_does_not_raise(self):
        from src.services.audio.speech_queue import SpeechQueue

        q = SpeechQueue()
        try:
            q.interrupt()
        except Exception as e:
            pytest.fail(f"interrupt() on empty queue raised: {e}")


class TestDiscussionBudgetStop:
    def test_social_arbiter_has_budget_check(self):
        from src.features.home.social_arbiter.arbiter import SocialArbiter

        arbiter = SocialArbiter()
        assert hasattr(arbiter, "should_stop_discussion")

    def test_budget_stop_below_threshold_returns_false(self):
        from src.features.home.social_arbiter.arbiter import SocialArbiter

        arbiter = SocialArbiter()
        arbiter.discussion_turn = 2
        arbiter.max_discussion_turns = 10
        assert arbiter.should_stop_discussion() is False

    def test_budget_stop_at_max_returns_true(self):
        from src.features.home.social_arbiter.arbiter import SocialArbiter

        arbiter = SocialArbiter()
        arbiter.discussion_turn = 10
        arbiter.max_discussion_turns = 10
        assert arbiter.should_stop_discussion() is True

    def test_budget_stop_above_max_returns_true(self):
        from src.features.home.social_arbiter.arbiter import SocialArbiter

        arbiter = SocialArbiter()
        arbiter.discussion_turn = 15
        arbiter.max_discussion_turns = 10
        assert arbiter.should_stop_discussion() is True

    def test_discussion_turn_increments_on_agent_stat_update(self):
        from src.features.home.social_arbiter.arbiter import SocialArbiter

        arbiter = SocialArbiter()
        initial = arbiter.discussion_turn
        arbiter.update_agent_stats("lisa", 1.0)
        assert arbiter.discussion_turn == initial + 1
