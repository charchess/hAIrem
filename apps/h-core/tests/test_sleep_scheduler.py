import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


@pytest.fixture
def mock_consolidator():
    c = AsyncMock()
    c.consolidate = AsyncMock(return_value=5)
    c.apply_decay = AsyncMock(return_value=None)
    return c


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.publish_event = AsyncMock()
    return r


@pytest.mark.asyncio
async def test_scheduler_triggers_on_inactivity(mock_consolidator, mock_redis):
    from src.services.sleep_scheduler import SleepScheduler

    scheduler = SleepScheduler(mock_consolidator, mock_redis, inactivity_threshold_minutes=0)
    scheduler.last_activity = datetime.utcnow() - timedelta(minutes=1)

    await scheduler._maybe_run_cycle()

    mock_consolidator.consolidate.assert_called_once()
    mock_consolidator.apply_decay.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_does_not_trigger_during_activity(mock_consolidator, mock_redis):
    from src.services.sleep_scheduler import SleepScheduler

    scheduler = SleepScheduler(mock_consolidator, mock_redis, inactivity_threshold_minutes=30)
    scheduler.last_activity = datetime.utcnow()

    await scheduler._maybe_run_cycle()

    mock_consolidator.consolidate.assert_not_called()


@pytest.mark.asyncio
async def test_scheduler_does_not_trigger_twice_in_a_row(mock_consolidator, mock_redis):
    from src.services.sleep_scheduler import SleepScheduler

    scheduler = SleepScheduler(mock_consolidator, mock_redis, inactivity_threshold_minutes=0)
    scheduler.last_activity = datetime.utcnow() - timedelta(minutes=1)

    await scheduler._maybe_run_cycle()
    await scheduler._maybe_run_cycle()

    assert mock_consolidator.consolidate.call_count == 1


def test_scheduler_updates_last_activity(mock_consolidator, mock_redis):
    from src.services.sleep_scheduler import SleepScheduler

    scheduler = SleepScheduler(mock_consolidator, mock_redis)
    before = scheduler.last_activity

    scheduler.record_activity()

    assert scheduler.last_activity > before


@pytest.mark.asyncio
async def test_scheduler_force_run_ignores_threshold(mock_consolidator, mock_redis):
    from src.services.sleep_scheduler import SleepScheduler

    scheduler = SleepScheduler(mock_consolidator, mock_redis, inactivity_threshold_minutes=9999)

    await scheduler.force_run()

    mock_consolidator.consolidate.assert_called_once()
    mock_consolidator.apply_decay.assert_called_once()
