import pytest
from unittest.mock import AsyncMock, MagicMock


class TestMultiRoomAudioRouter:
    def test_resolve_speaker_known_room(self):
        from src.services.audio.multiroom_router import MultiRoomAudioRouter

        router = MultiRoomAudioRouter()
        assert router.resolve_speaker("salon") == "media_player.salon"
        assert router.resolve_speaker("cuisine") == "media_player.cuisine"
        assert router.resolve_speaker("chambre") == "media_player.chambre"
        assert router.resolve_speaker("bureau") == "media_player.bureau"

    def test_resolve_speaker_case_insensitive(self):
        from src.services.audio.multiroom_router import MultiRoomAudioRouter

        router = MultiRoomAudioRouter()
        assert router.resolve_speaker("Salon") == "media_player.salon"
        assert router.resolve_speaker("CUISINE") == "media_player.cuisine"

    def test_resolve_speaker_unknown_room_returns_none(self):
        from src.services.audio.multiroom_router import MultiRoomAudioRouter

        router = MultiRoomAudioRouter()
        assert router.resolve_speaker("garage") is None
        assert router.resolve_speaker(None) is None

    def test_get_speakers_for_room_returns_list(self):
        from src.services.audio.multiroom_router import MultiRoomAudioRouter

        router = MultiRoomAudioRouter()
        speakers = router.get_speakers_for_room("salon")
        assert speakers == ["media_player.salon"]

    def test_get_speakers_for_unknown_room_returns_empty(self):
        from src.services.audio.multiroom_router import MultiRoomAudioRouter

        router = MultiRoomAudioRouter()
        speakers = router.get_speakers_for_room("jardin")
        assert speakers == []

    async def test_route_calls_ha_play_media(self):
        from src.services.audio.multiroom_router import MultiRoomAudioRouter

        ha = MagicMock()
        ha.call_service = AsyncMock(return_value=True)
        router = MultiRoomAudioRouter(ha_client=ha)

        result = await router.route("http://audio.mp3", room_id="salon", agent_id="lisa")

        assert result is True
        ha.call_service.assert_called_once_with(
            "media_player",
            "play_media",
            {
                "entity_id": "media_player.salon",
                "media_content_id": "http://audio.mp3",
                "media_content_type": "music",
            },
        )

    async def test_route_unknown_room_returns_false(self):
        from src.services.audio.multiroom_router import MultiRoomAudioRouter

        ha = MagicMock()
        ha.call_service = AsyncMock()
        router = MultiRoomAudioRouter(ha_client=ha)

        result = await router.route("http://audio.mp3", room_id="jardin", agent_id="renarde")

        assert result is False
        ha.call_service.assert_not_called()

    async def test_route_without_ha_client_returns_false(self):
        from src.services.audio.multiroom_router import MultiRoomAudioRouter

        router = MultiRoomAudioRouter(ha_client=None)
        result = await router.route("http://audio.mp3", room_id="salon")
        assert result is False

    def test_custom_room_speaker_map(self):
        from src.services.audio.multiroom_router import MultiRoomAudioRouter

        custom_map = {"salle_de_bain": "media_player.bathroom"}
        router = MultiRoomAudioRouter(room_speaker_map=custom_map)
        assert router.resolve_speaker("salle_de_bain") == "media_player.bathroom"
        assert router.resolve_speaker("salon") is None


class TestSpeechRequestRoomId:
    async def test_speech_request_has_room_id_field(self):
        from src.services.audio.speech_queue import SpeechRequest

        req = SpeechRequest(text="hello", agent_id="lisa", room_id="salon")
        assert req.room_id == "salon"

    async def test_speech_request_room_id_defaults_to_none(self):
        from src.services.audio.speech_queue import SpeechRequest

        req = SpeechRequest(text="bonjour", agent_id="renarde")
        assert req.room_id is None

    async def test_speech_queue_preserves_room_id(self):
        from src.services.audio.speech_queue import SpeechQueue, SpeechRequest

        q = SpeechQueue()
        req = SpeechRequest(text="test", agent_id="lisa", room_id="bureau")
        await q.enqueue(req)
        dequeued = await q.dequeue()
        assert dequeued.room_id == "bureau"
