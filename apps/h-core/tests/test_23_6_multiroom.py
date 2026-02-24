import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestLocationServiceUserRoom:
    @pytest.mark.asyncio
    async def test_get_user_room_returns_room_from_ha(self):
        from src.features.home.spatial.location.service import LocationService

        ha = MagicMock()
        ha.get_state = AsyncMock(return_value="salon")
        surreal = MagicMock()
        svc = LocationService(surreal_client=surreal)

        result = await svc.get_user_room(ha_client=ha)

        assert result == "salon"
        ha.get_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_room_returns_none_when_not_home(self):
        from src.features.home.spatial.location.service import LocationService

        ha = MagicMock()
        ha.get_state = AsyncMock(return_value="not_home")
        surreal = MagicMock()
        svc = LocationService(surreal_client=surreal)

        result = await svc.get_user_room(ha_client=ha)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_room_returns_none_when_ha_unavailable(self):
        from src.features.home.spatial.location.service import LocationService

        surreal = MagicMock()
        svc = LocationService(surreal_client=surreal)

        result = await svc.get_user_room(ha_client=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_room_returns_none_on_ha_error(self):
        from src.features.home.spatial.location.service import LocationService

        ha = MagicMock()
        ha.get_state = AsyncMock(side_effect=Exception("HA unreachable"))
        surreal = MagicMock()
        svc = LocationService(surreal_client=surreal)

        result = await svc.get_user_room(ha_client=ha)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_room_accepts_custom_entity_id(self):
        from src.features.home.spatial.location.service import LocationService

        ha = MagicMock()
        ha.get_state = AsyncMock(return_value="cuisine")
        surreal = MagicMock()
        svc = LocationService(surreal_client=surreal)

        result = await svc.get_user_room(ha_client=ha, entity_id="input_select.user_location")

        ha.get_state.assert_called_once_with("input_select.user_location")
        assert result == "cuisine"


class TestTtsRoomRouting:
    @pytest.mark.asyncio
    async def test_synthesize_and_broadcast_routes_to_agent_room(self):
        from src.services.audio.tts_orchestrator import TtsOrchestrator

        primary = MagicMock()
        primary.synthesize = AsyncMock(return_value=b"audio")
        fallback = MagicMock()
        redis = MagicMock()
        redis.publish_event = AsyncMock()

        router = MagicMock()
        router.route = AsyncMock(return_value=True)

        orch = TtsOrchestrator(primary=primary, fallback=fallback, redis_client=redis, room_router=router)
        await orch.synthesize_and_broadcast("Bonjour", agent_id="lisa", voice_id="FR", room_id="salon")

        router.route.assert_called_once()
        call_args = router.route.call_args
        assert call_args[1].get("room_id") == "salon" or call_args[0][1] == "salon"

    @pytest.mark.asyncio
    async def test_synthesize_and_broadcast_skips_routing_without_room_id(self):
        from src.services.audio.tts_orchestrator import TtsOrchestrator

        primary = MagicMock()
        primary.synthesize = AsyncMock(return_value=b"audio")
        fallback = MagicMock()
        redis = MagicMock()
        redis.publish_event = AsyncMock()

        router = MagicMock()
        router.route = AsyncMock(return_value=True)

        orch = TtsOrchestrator(primary=primary, fallback=fallback, redis_client=redis, room_router=router)
        await orch.synthesize_and_broadcast("Bonjour", agent_id="lisa", voice_id="FR")

        router.route.assert_not_called()

    @pytest.mark.asyncio
    async def test_synthesize_and_broadcast_skips_routing_without_router(self):
        from src.services.audio.tts_orchestrator import TtsOrchestrator

        primary = MagicMock()
        primary.synthesize = AsyncMock(return_value=b"audio")
        fallback = MagicMock()
        redis = MagicMock()
        redis.publish_event = AsyncMock()

        orch = TtsOrchestrator(primary=primary, fallback=fallback, redis_client=redis)
        await orch.synthesize_and_broadcast("Bonjour", agent_id="lisa", voice_id="FR", room_id="salon")

        redis.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_tts_router_does_not_block_redis_broadcast(self):
        from src.services.audio.tts_orchestrator import TtsOrchestrator

        primary = MagicMock()
        primary.synthesize = AsyncMock(return_value=b"audio")
        fallback = MagicMock()
        redis = MagicMock()
        redis.publish_event = AsyncMock()

        router = MagicMock()
        router.route = AsyncMock(return_value=True)

        orch = TtsOrchestrator(primary=primary, fallback=fallback, redis_client=redis, room_router=router)
        await orch.synthesize_and_broadcast("Bonjour", agent_id="lisa", voice_id="FR", room_id="salon")

        redis.publish_event.assert_called_once()


class TestUserLocationArbiterBoost:
    @pytest.mark.asyncio
    async def test_user_location_passed_to_arbiter_world_context(self):
        from src.main import HaremOrchestrator

        orch = HaremOrchestrator.__new__(HaremOrchestrator)
        orch.discussion_budget = 5
        orch.MAX_DISCUSSION_BUDGET = 5
        orch.agent_registry = MagicMock()
        orch.agent_registry.agents = {}

        captured_contexts = []

        async def capture_context(content, world_context=None, **kwargs):
            captured_contexts.append(world_context)
            return None

        orch.social_arbiter = MagicMock()
        orch.social_arbiter.determine_responder_async = AsyncMock(side_effect=capture_context)
        orch.redis = MagicMock()
        orch.redis.publish = AsyncMock()
        orch.surreal = MagicMock()
        orch.speech_queue = MagicMock()
        orch.speech_queue.is_speaking = False

        from src.services.audio.speech_queue import SpeechQueue

        orch.speech_queue = SpeechQueue()

        orch.world_state = MagicMock()
        orch.world_state.get_theme = MagicMock(return_value="Default")

        orch.user_room = "cuisine"

        data = {
            "type": "user_message",
            "sender": {"agent_id": "user", "role": "user"},
            "recipient": {"target": "broadcast"},
            "payload": {"content": "Bonjour"},
            "id": str(uuid4()),
        }

        await orch.handle_message(data)

        assert len(captured_contexts) == 1
        assert captured_contexts[0] is not None
        assert captured_contexts[0].get("location") == "cuisine"

    @pytest.mark.asyncio
    async def test_user_room_defaults_to_none_when_unset(self):
        from src.main import HaremOrchestrator

        orch = HaremOrchestrator.__new__(HaremOrchestrator)
        orch.discussion_budget = 5
        orch.MAX_DISCUSSION_BUDGET = 5
        orch.agent_registry = MagicMock()
        orch.agent_registry.agents = {}

        captured_contexts = []

        async def capture_context(content, world_context=None, **kwargs):
            captured_contexts.append(world_context)
            return None

        orch.social_arbiter = MagicMock()
        orch.social_arbiter.determine_responder_async = AsyncMock(side_effect=capture_context)
        orch.redis = MagicMock()
        orch.redis.publish = AsyncMock()
        orch.surreal = MagicMock()
        orch.speech_queue = MagicMock()
        orch.speech_queue.is_speaking = False

        from src.services.audio.speech_queue import SpeechQueue

        orch.speech_queue = SpeechQueue()

        orch.world_state = MagicMock()
        orch.world_state.get_theme = MagicMock(return_value="Default")

        data = {
            "type": "user_message",
            "sender": {"agent_id": "user", "role": "user"},
            "recipient": {"target": "broadcast"},
            "payload": {"content": "Bonjour"},
            "id": str(uuid4()),
        }

        await orch.handle_message(data)

        assert len(captured_contexts) == 1
        assert captured_contexts[0] is not None
        assert captured_contexts[0].get("location") is None
