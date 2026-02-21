import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_detector(redis=None):
    from src.features.home.wakeword.wakeword import WakewordDetector

    event_bus = MagicMock()
    event_bus.publish = AsyncMock()
    if redis is None:
        redis = MagicMock()
        redis.publish_event = AsyncMock()
    return WakewordDetector(
        config={"wakeword": "hey_lisa", "threshold": 0.5},
        event_bus=event_bus,
        redis_client=redis,
    )


def test_wakeword_detector_initializes_without_crash():
    detector = _make_detector()
    assert detector is not None
    assert detector.engine is None


def test_process_audio_returns_none_when_engine_unavailable():
    detector = _make_detector()
    result = detector.process_audio(b"\x00" * 1280)
    assert result is None


def test_process_audio_returns_none_on_empty_buffer():
    detector = _make_detector()
    result = detector.process_audio(b"")
    assert result is None


def test_process_audio_returns_agent_name_when_model_detects():
    detector = _make_detector()

    mock_engine = MagicMock()
    mock_engine.model = MagicMock()
    mock_engine.threshold = 0.5
    mock_engine.model.predict = MagicMock(return_value={"hey_lisa": 0.9})
    detector.engine = mock_engine

    with patch("src.features.home.wakeword.wakeword.OPENWAKEWORD_AVAILABLE", True):
        with patch("src.features.home.wakeword.wakeword.np") as mock_np:
            mock_np.frombuffer = MagicMock(return_value=MagicMock())
            mock_np.frombuffer.return_value.astype = MagicMock(return_value=MagicMock())
            result = detector.process_audio(b"\x00" * 1280)

    assert result == "Lisa"


def test_process_audio_returns_none_below_threshold():
    detector = _make_detector()

    mock_engine = MagicMock()
    mock_engine.model = MagicMock()
    mock_engine.threshold = 0.5
    mock_engine.model.predict = MagicMock(return_value={"hey_lisa": 0.1})
    detector.engine = mock_engine

    with patch("src.features.home.wakeword.wakeword.OPENWAKEWORD_AVAILABLE", True):
        with patch("src.features.home.wakeword.wakeword.np") as mock_np:
            mock_np.frombuffer = MagicMock(return_value=MagicMock())
            mock_np.frombuffer.return_value.astype = MagicMock(return_value=MagicMock())
            result = detector.process_audio(b"\x00" * 1280)

    assert result is None


@pytest.mark.asyncio
async def test_wakeword_publishes_hlink_on_detection():
    redis = MagicMock()
    redis.publish_event = AsyncMock()
    detector = _make_detector(redis=redis)

    detection_info = {"wakeword": "hey_lisa", "confidence": 0.9, "timestamp": 0.0}
    await detector._on_wakeword_detected(detection_info)

    redis.publish_event.assert_called_once()
    call_args = redis.publish_event.call_args[0]
    assert call_args[0] == "conversation_stream"
    assert call_args[1]["type"] == "user_message"


@pytest.mark.asyncio
async def test_wakeword_service_lifecycle_start_stop():
    from src.features.home.wakeword.service import WakewordService

    redis = MagicMock()
    redis.publish = AsyncMock()
    surreal = MagicMock()
    config = {"wakeword": {"wakeword": "hey_lisa", "threshold": 0.5}}

    service = WakewordService(config, redis, surreal)
    assert not service.is_active
    await service.stop()
    assert not service.is_active
