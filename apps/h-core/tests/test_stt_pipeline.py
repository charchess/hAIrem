import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


def _make_stt(model=None):
    from src.services.audio.stt_service import SttService

    svc = SttService.__new__(SttService)
    svc.model_size = "base"
    svc.device = "cpu"
    svc._model = model
    return svc


def test_stt_service_initializes_without_crash():
    from src.services.audio.stt_service import SttService

    svc = SttService()
    assert svc is not None


@pytest.mark.asyncio
async def test_transcribe_returns_empty_on_no_bytes():
    svc = _make_stt(model=None)
    result = await svc.transcribe(b"")
    assert result == ""


@pytest.mark.asyncio
async def test_transcribe_returns_empty_when_model_unavailable():
    svc = _make_stt(model=None)
    result = await svc.transcribe(b"\x00" * 1024)
    assert result == ""


@pytest.mark.asyncio
async def test_transcribe_calls_model_when_available():
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "Bonjour"
    mock_model.transcribe = MagicMock(return_value=([mock_segment], None))

    svc = _make_stt(model=mock_model)

    with patch("tempfile.NamedTemporaryFile") as mock_tmp, patch("os.unlink"):
        mock_tmp.return_value.__enter__ = MagicMock(return_value=MagicMock(name="f"))
        mock_tmp.return_value.__exit__ = MagicMock(return_value=False)
        mock_tmp.return_value.__enter__.return_value.name = "/tmp/fake.wav"

        result = await svc.transcribe(b"\x00" * 1024)

    assert mock_model.transcribe.called


@pytest.mark.asyncio
async def test_transcribe_returns_empty_on_exception():
    mock_model = MagicMock()
    mock_model.transcribe = MagicMock(side_effect=Exception("whisper error"))

    svc = _make_stt(model=mock_model)

    with patch("tempfile.NamedTemporaryFile") as mock_tmp, patch("os.unlink"):
        mock_tmp.return_value.__enter__ = MagicMock(return_value=MagicMock(name="f"))
        mock_tmp.return_value.__exit__ = MagicMock(return_value=False)
        mock_tmp.return_value.__enter__.return_value.name = "/tmp/fake.wav"

        result = await svc.transcribe(b"\x00" * 1024)

    assert result == ""


@pytest.mark.asyncio
async def test_transcribe_and_publish_creates_hlink_message():
    svc = _make_stt()
    svc.transcribe = AsyncMock(return_value="Bonjour")

    redis = MagicMock()
    redis.publish_event = AsyncMock()

    result = await svc.transcribe_and_publish(b"\x00" * 100, "session-1", redis)

    assert result == "Bonjour"
    redis.publish_event.assert_called_once()
    call_args = redis.publish_event.call_args[0]
    assert call_args[0] == "conversation_stream"
    assert call_args[1]["type"] == "user_message"


@pytest.mark.asyncio
async def test_transcribe_and_publish_skips_empty_transcription():
    svc = _make_stt()
    svc.transcribe = AsyncMock(return_value="")

    redis = MagicMock()
    redis.publish_event = AsyncMock()

    result = await svc.transcribe_and_publish(b"\x00" * 100, "session-1", redis)

    assert result is None
    redis.publish_event.assert_not_called()
