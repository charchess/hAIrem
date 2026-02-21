import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_speech_queue_enqueue_dequeue_fifo():
    from src.services.audio.speech_queue import SpeechQueue, SpeechRequest

    q = SpeechQueue()
    for i in range(3):
        await q.enqueue(SpeechRequest(text=f"msg{i}", agent_id="lisa", priority=1))
    results = [await q.dequeue() for _ in range(3)]
    assert [r.text for r in results] == ["msg0", "msg1", "msg2"]


@pytest.mark.asyncio
async def test_speech_queue_user_priority_before_agent():
    from src.services.audio.speech_queue import SpeechQueue, SpeechRequest

    q = SpeechQueue()
    await q.enqueue(SpeechRequest(text="agent_msg", agent_id="lisa", priority=1))
    await q.enqueue(SpeechRequest(text="user_msg", agent_id="user", priority=0))
    first = await q.dequeue()
    assert first.text == "user_msg"


@pytest.mark.asyncio
async def test_speech_queue_qsize():
    from src.services.audio.speech_queue import SpeechQueue, SpeechRequest

    q = SpeechQueue()
    assert q.qsize() == 0
    await q.enqueue(SpeechRequest(text="hello", agent_id="lisa", priority=1))
    assert q.qsize() == 1


@pytest.mark.asyncio
async def test_speech_queue_stop_sets_event():
    from src.services.audio.speech_queue import SpeechQueue

    q = SpeechQueue()
    q.stop()
    assert q._stop_event.is_set()


@pytest.mark.asyncio
async def test_melotts_provider_calls_post():
    from src.services.audio.melotts_provider import MeloTtsProvider

    provider = MeloTtsProvider(base_url="http://mock-melotts")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"audio_data"

    with patch("src.services.audio.melotts_provider.httpx") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client

        result = await provider.synthesize("Bonjour", "FR")
        assert result == b"audio_data"
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_melotts_provider_returns_empty_on_timeout():
    from src.services.audio.melotts_provider import MeloTtsProvider
    import httpx

    provider = MeloTtsProvider(base_url="http://mock-melotts")

    with patch("src.services.audio.melotts_provider.httpx") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=Exception("timeout"))
        mock_httpx.AsyncClient.return_value = mock_client

        result = await provider.synthesize("Bonjour", "FR")
        assert result == b""


@pytest.mark.asyncio
async def test_melotts_returns_empty_on_empty_text():
    from src.services.audio.melotts_provider import MeloTtsProvider

    provider = MeloTtsProvider()
    result = await provider.synthesize("", "FR")
    assert result == b""


@pytest.mark.asyncio
async def test_elevenlabs_returns_empty_without_api_key():
    from src.services.audio.elevenlabs_provider import ElevenLabsProvider

    provider = ElevenLabsProvider(api_key="")
    result = await provider.synthesize("Bonjour", "voice-123")
    assert result == b""


@pytest.mark.asyncio
async def test_elevenlabs_returns_empty_on_empty_text():
    from src.services.audio.elevenlabs_provider import ElevenLabsProvider

    provider = ElevenLabsProvider(api_key="test-key")
    result = await provider.synthesize("", "voice-123")
    assert result == b""


@pytest.mark.asyncio
async def test_tts_orchestrator_falls_back_on_primary_failure():
    from src.services.audio.tts_orchestrator import TtsOrchestrator

    primary = MagicMock()
    primary.synthesize = AsyncMock(return_value=b"")
    fallback = MagicMock()
    fallback.synthesize = AsyncMock(return_value=b"fallback_audio")
    redis = MagicMock()
    redis.publish_event = AsyncMock()

    orch = TtsOrchestrator(primary=primary, fallback=fallback, redis_client=redis)
    result = await orch.synthesize("Bonjour", "FR")

    assert result == b"fallback_audio"
    fallback.synthesize.assert_called_once()


@pytest.mark.asyncio
async def test_tts_orchestrator_uses_primary_when_available():
    from src.services.audio.tts_orchestrator import TtsOrchestrator

    primary = MagicMock()
    primary.synthesize = AsyncMock(return_value=b"primary_audio")
    fallback = MagicMock()
    fallback.synthesize = AsyncMock(return_value=b"fallback_audio")
    redis = MagicMock()
    redis.publish_event = AsyncMock()

    orch = TtsOrchestrator(primary=primary, fallback=fallback, redis_client=redis)
    result = await orch.synthesize("Bonjour", "FR")

    assert result == b"primary_audio"
    fallback.synthesize.assert_not_called()


@pytest.mark.asyncio
async def test_tts_orchestrator_broadcasts_to_redis():
    from src.services.audio.tts_orchestrator import TtsOrchestrator

    primary = MagicMock()
    primary.synthesize = AsyncMock(return_value=b"audio")
    fallback = MagicMock()
    fallback.synthesize = AsyncMock(return_value=b"")
    redis = MagicMock()
    redis.publish_event = AsyncMock()

    orch = TtsOrchestrator(primary=primary, fallback=fallback, redis_client=redis)
    await orch.synthesize_and_broadcast("Bonjour", "lisa", "FR-Lisa")

    redis.publish_event.assert_called_once()
    call_args = redis.publish_event.call_args[0]
    assert call_args[0] == "system_stream"
    assert "audio_b64" in call_args[1]["payload"]["content"]


@pytest.mark.asyncio
async def test_tts_orchestrator_skips_broadcast_on_empty_audio():
    from src.services.audio.tts_orchestrator import TtsOrchestrator

    primary = MagicMock()
    primary.synthesize = AsyncMock(return_value=b"")
    fallback = MagicMock()
    fallback.synthesize = AsyncMock(return_value=b"")
    redis = MagicMock()
    redis.publish_event = AsyncMock()

    orch = TtsOrchestrator(primary=primary, fallback=fallback, redis_client=redis)
    await orch.synthesize_and_broadcast("Bonjour", "lisa", "FR-Lisa")

    redis.publish_event.assert_not_called()
