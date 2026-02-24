import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


class TestSpeechQueueBargeIn:
    def test_speech_queue_has_is_speaking_false_by_default(self):
        from src.services.audio.speech_queue import SpeechQueue

        q = SpeechQueue()
        assert q.is_speaking is False

    def test_speech_queue_has_current_speaker_none_by_default(self):
        from src.services.audio.speech_queue import SpeechQueue

        q = SpeechQueue()
        assert q.current_speaker is None

    def test_set_speaking_marks_queue_active(self):
        from src.services.audio.speech_queue import SpeechQueue

        q = SpeechQueue()
        q.set_speaking("lisa")
        assert q.is_speaking is True
        assert q.current_speaker == "lisa"

    def test_interrupt_clears_speaking_state(self):
        from src.services.audio.speech_queue import SpeechQueue

        q = SpeechQueue()
        q.set_speaking("lisa")
        q.interrupt()
        assert q.is_speaking is False
        assert q.current_speaker is None


class TestBargeInOrchestrator:
    def _make_orch(self, is_speaking: bool = True, current_speaker: str = "lisa"):
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
        orch.redis.publish_event = AsyncMock()
        orch.surreal = MagicMock()

        from src.services.audio.speech_queue import SpeechQueue

        orch.speech_queue = SpeechQueue()
        if is_speaking:
            orch.speech_queue.set_speaking(current_speaker)
        return orch

    @pytest.mark.asyncio
    async def test_barge_in_calls_interrupt_when_speaking(self):
        orch = self._make_orch(is_speaking=True, current_speaker="lisa")
        data = {
            "type": "audio.barge_in",
            "sender": {"agent_id": "system", "role": "system"},
            "recipient": {"target": "system"},
            "payload": {"content": {}},
            "id": str(uuid4()),
        }
        await orch.handle_message(data)
        assert orch.speech_queue.is_speaking is False

    @pytest.mark.asyncio
    async def test_barge_in_publishes_acknowledgment(self):
        orch = self._make_orch(is_speaking=True, current_speaker="lisa")
        data = {
            "type": "audio.barge_in",
            "sender": {"agent_id": "system", "role": "system"},
            "recipient": {"target": "system"},
            "payload": {"content": {}},
            "id": str(uuid4()),
        }
        await orch.handle_message(data)
        orch.redis.publish_event.assert_called_once()
        call_args = orch.redis.publish_event.call_args[0]
        assert call_args[0] == "system_stream"
        payload = call_args[1]
        assert payload.get("type") == "agent.interrupted"
        assert payload["payload"]["content"]["agent_id"] == "lisa"

    @pytest.mark.asyncio
    async def test_barge_in_ignored_when_not_speaking(self):
        orch = self._make_orch(is_speaking=False)
        data = {
            "type": "audio.barge_in",
            "sender": {"agent_id": "system", "role": "system"},
            "recipient": {"target": "system"},
            "payload": {"content": {}},
            "id": str(uuid4()),
        }
        await orch.handle_message(data)
        orch.redis.publish_event.assert_not_called()


class TestWakewordBargeIn:
    @pytest.mark.asyncio
    async def test_emit_barge_in_publishes_to_system_stream(self):
        from src.features.home.wakeword.service import WakewordService

        mock_redis = MagicMock()
        mock_redis.publish_event = AsyncMock()
        mock_surreal = MagicMock()

        svc = WakewordService(config={}, redis_client=mock_redis, surreal_client=mock_surreal)
        await svc.emit_barge_in()

        mock_redis.publish_event.assert_called_once()
        call_args = mock_redis.publish_event.call_args[0]
        assert call_args[0] == "system_stream"
        assert call_args[1]["type"] == "audio.barge_in"

    @pytest.mark.asyncio
    async def test_emit_barge_in_only_when_tts_active(self):
        from src.features.home.wakeword.service import WakewordService

        mock_redis = MagicMock()
        mock_redis.publish_event = AsyncMock()
        mock_surreal = MagicMock()

        svc = WakewordService(config={}, redis_client=mock_redis, surreal_client=mock_surreal)

        from src.services.audio.speech_queue import SpeechQueue

        speech_queue = SpeechQueue()

        await svc.emit_barge_in(speech_queue=speech_queue)
        mock_redis.publish_event.assert_not_called()

        speech_queue.set_speaking("lisa")
        await svc.emit_barge_in(speech_queue=speech_queue)
        mock_redis.publish_event.assert_called_once()
