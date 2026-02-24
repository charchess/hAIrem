import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock

pytestmark = pytest.mark.asyncio


async def _make_handler():
    from src.main import RedisLogHandler

    mock_redis = MagicMock()
    mock_redis.publish_event = AsyncMock()
    handler = RedisLogHandler(mock_redis)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    handler.setLevel(logging.WARNING)
    return handler, mock_redis


def _make_record(msg="test log", level=logging.WARNING):
    return logging.LogRecord(
        name="test",
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )


async def test_emit_puts_to_queue():
    handler, _ = await _make_handler()
    handler.emit(_make_record("hello"))
    assert not handler._queue.empty()
    assert "hello" in handler._queue.get_nowait()


async def test_emit_does_not_call_redis_directly():
    handler, mock_redis = await _make_handler()
    handler.emit(_make_record("direct test"))
    mock_redis.publish_event.assert_not_called()


async def test_emit_below_level_ignored():
    handler, _ = await _make_handler()
    handler.emit(_make_record("debug", level=logging.DEBUG))
    assert handler._queue.empty()


async def test_emit_is_synchronous_no_await():
    handler, _ = await _make_handler()
    for i in range(10):
        handler.emit(_make_record(f"msg {i}"))
    count = 0
    while not handler._queue.empty():
        handler._queue.get_nowait()
        count += 1
    assert count == 10


async def test_worker_publishes_to_system_stream():
    handler, mock_redis = await _make_handler()
    handler.emit(_make_record("important warning"))

    stop = asyncio.Event()
    worker = asyncio.create_task(handler.start_worker(stop_event=stop))
    await asyncio.sleep(0.15)
    stop.set()
    await worker

    mock_redis.publish_event.assert_called_once()
    args = mock_redis.publish_event.call_args[0]
    assert args[0] == "system_stream"
    assert args[1]["type"] == "system.log"
    assert "important warning" in args[1]["payload"]["content"]


async def test_worker_drains_multiple_records():
    handler, mock_redis = await _make_handler()
    for i in range(3):
        handler.emit(_make_record(f"msg {i}"))

    stop = asyncio.Event()
    worker = asyncio.create_task(handler.start_worker(stop_event=stop))
    await asyncio.sleep(0.15)
    stop.set()
    await worker

    assert mock_redis.publish_event.call_count == 3
    assert handler._queue.empty()


async def test_worker_survives_publish_error():
    handler, mock_redis = await _make_handler()
    mock_redis.publish_event = AsyncMock(side_effect=Exception("Redis down"))
    handler.emit(_make_record("log during outage"))

    stop = asyncio.Event()
    worker = asyncio.create_task(handler.start_worker(stop_event=stop))
    await asyncio.sleep(0.15)
    stop.set()
    await worker

    assert handler._queue.empty()
