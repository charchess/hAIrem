import pytest
from src.services.ha_event_worker import HaEventWorker
from electra.drivers.ha_client import HaClient
from src.infrastructure.redis import RedisClient
from unittest.mock import AsyncMock, MagicMock, ANY


@pytest.fixture
def mock_redis():
    mock = MagicMock(spec=RedisClient)
    mock.publish_event = AsyncMock()
    return mock


@pytest.fixture
def mock_ha():
    return MagicMock(spec=HaClient)


@pytest.mark.asyncio
async def test_process_event(mock_redis: RedisClient, mock_ha: HaClient):
    worker = HaEventWorker(mock_redis, mock_ha)
    event = {"event_type": "state_changed", "data": {"entity_id": "light.kitchen", "new_state": {"state": "on"}}}
    await worker.process_event(event)
    # Assert publish_event was called with expected message
    mock_redis.publish_event.assert_called_with("system_stream", ANY)  # Check payload
