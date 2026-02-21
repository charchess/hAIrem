import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

# TDD: Epic 10 - Proactivity Triggers
# Tests for Hardware Events and System Stimulus.
# Requirements: FR53 (Hardware Events), FR55 (System Stimulus).


class TestProactivityTriggers:
    @pytest.mark.asyncio
    async def test_hardware_event_reaction(self):
        # FR53: Hardware Events
        # When a hardware event occurs (e.g. "Doorbell Ring"), the proactive engine
        # should trigger relevant agents.

        redis = MagicMock()
        surreal = MagicMock()
        redis.publish_event = AsyncMock()

        from src.services.proactivity.engine import ProactivityEngine

        engine = ProactivityEngine(redis, surreal)

        # Define: Event "doorbell_ring" -> Trigger "Lisa" (Greeter)
        await engine.register_trigger("doorbell_ring", "Lisa")

        # Action: Fire Event
        await engine.process_event({"type": "hardware", "name": "doorbell_ring"})

        # Assert: Redis message sent to Lisa
        redis.publish_event.assert_called()
        msg = redis.publish_event.call_args[0][1]
        assert "Lisa" in str(msg)
        assert "doorbell" in str(msg).lower()

    @pytest.mark.asyncio
    async def test_system_stimulus_reaction(self):
        # FR55: System Stimulus
        # When a scheduled system event occurs (e.g. "Wake Up"), the system should react.

        redis = MagicMock()
        surreal = MagicMock()
        redis.publish_event = AsyncMock()

        from src.services.proactivity.engine import ProactivityEngine

        engine = ProactivityEngine(redis, surreal)

        # Define: Stimulus "morning_routine"
        await engine.register_stimulus("morning_routine", ["Lisa", "Electra"])

        # Action: Fire Stimulus
        await engine.trigger_stimulus("morning_routine")

        # Assert: Broadcast to multiple agents
        assert redis.publish_event.call_count >= 2
