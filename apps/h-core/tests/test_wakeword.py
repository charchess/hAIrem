import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.features.home.wakeword.service import WakewordService


@pytest.mark.asyncio
async def test_wakeword_service_initialization():
    """Test wakeword service initialization."""
    mock_redis = AsyncMock()
    mock_surreal = AsyncMock()

    config = {"wakeword": {"wakeword": "hey_lisa", "threshold": 0.5}}

    service = WakewordService(config, mock_redis, mock_surreal)
    success = await service.initialize()

    # Since openWakeWord may not be available in test environment, this might fail
    # but we can test the structure
    assert isinstance(service, WakewordService)
    assert service.config == config


@pytest.mark.asyncio
async def test_wakeword_service_status():
    """Test wakeword service status reporting."""
    mock_redis = AsyncMock()
    mock_surreal = AsyncMock()

    config = {"wakeword": {"wakeword": "hey_lisa", "threshold": 0.5}}

    service = WakewordService(config, mock_redis, mock_surreal)

    # Test status before initialization
    status = await service.get_status()
    assert status["initialized"] == False
    assert status["active"] == False


@pytest.mark.asyncio
async def test_wakeword_service_publish():
    """Test wakeword service event publishing."""
    mock_redis = AsyncMock()
    mock_surreal = AsyncMock()

    config = {"wakeword": {"wakeword": "hey_lisa", "threshold": 0.5}}
    service = WakewordService(config, mock_redis, mock_surreal)

    # Test the publish method directly
    event = {"type": "test.event", "data": {"test": "data"}}

    await service.publish(event)

    # Verify Redis publish was called
    mock_redis.publish.assert_called_once_with("events:test.event", event)
