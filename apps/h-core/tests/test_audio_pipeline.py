import pytest
from unittest.mock import AsyncMock, MagicMock


def _make_pipeline(transcription="", user_id=None):
    from src.services.audio.audio_pipeline import AudioPipeline
    from src.features.home.voice_recognition.models import SessionUser

    stt = MagicMock()
    stt.transcribe = AsyncMock(return_value=transcription)

    session_user = SessionUser(
        session_id="test-session",
        user_id=user_id,
        is_anonymous=(user_id is None),
    )
    voice_rec = MagicMock()
    voice_rec.process_session_voice = AsyncMock(return_value=session_user)

    redis = MagicMock()
    redis.publish_event = AsyncMock()

    return AudioPipeline(stt_service=stt, voice_recognition=voice_rec, redis_client=redis), redis


@pytest.mark.asyncio
async def test_audio_pipeline_full_flow_publishes_hlink():
    pipeline, redis = _make_pipeline(transcription="Bonjour")
    result = await pipeline.process_audio_chunk(b"\x00" * 100, "session-1")

    assert result == "Bonjour"
    redis.publish_event.assert_called_once()
    args = redis.publish_event.call_args[0]
    assert args[0] == "conversation_stream"
    assert args[1]["type"] == "user_message"


@pytest.mark.asyncio
async def test_audio_pipeline_empty_transcription_no_publish():
    pipeline, redis = _make_pipeline(transcription="")
    result = await pipeline.process_audio_chunk(b"\x00" * 100, "session-1")

    assert result is None
    redis.publish_event.assert_not_called()


@pytest.mark.asyncio
async def test_audio_pipeline_injects_identified_user_id():
    pipeline, redis = _make_pipeline(transcription="Allume la lumière", user_id="user-42")
    await pipeline.process_audio_chunk(b"\x00" * 100, "session-1")

    payload = redis.publish_event.call_args[0][1]
    assert payload["payload"]["content"]["user_id"] == "user-42"


@pytest.mark.asyncio
async def test_audio_pipeline_anonymous_on_no_recognition():
    pipeline, redis = _make_pipeline(transcription="Bonjour", user_id=None)
    await pipeline.process_audio_chunk(b"\x00" * 100, "session-1")

    payload = redis.publish_event.call_args[0][1]
    assert payload["sender"]["agent_id"] == "anonymous"


@pytest.mark.asyncio
async def test_audio_pipeline_session_id_in_payload():
    pipeline, redis = _make_pipeline(transcription="Test", user_id="user-1")
    await pipeline.process_audio_chunk(b"\x00" * 100, "my-session")

    payload = redis.publish_event.call_args[0][1]
    assert payload["payload"]["content"]["session_id"] == "my-session"
