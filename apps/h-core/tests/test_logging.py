import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, patch, MagicMock
from src.models.hlink import MessageType
from src.main import RedisLogHandler


@pytest.mark.asyncio
async def test_redis_log_handler_publishes_to_redis():
    mock_redis = AsyncMock()
    mock_redis.publish_event = AsyncMock()
    handler = RedisLogHandler(mock_redis)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    handler.setLevel(logging.WARNING)

    logger = logging.getLogger("test_logger_23_7")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    stop = asyncio.Event()
    worker = asyncio.create_task(handler.start_worker(stop_event=stop))

    try:
        logger.warning("Test message")
        await asyncio.sleep(0.15)
        stop.set()
        await worker

        mock_redis.publish_event.assert_called_once()
        args, kwargs = mock_redis.publish_event.call_args
        assert args[0] == "system_stream"
        message_data = args[1]
        assert message_data["type"] == "system.log"
        assert "Test message" in message_data["payload"]["content"]
    finally:
        logger.removeHandler(handler)


@pytest.mark.asyncio
async def test_redis_log_handler_prevents_recursion_and_noise():
    mock_redis = AsyncMock()
    handler = RedisLogHandler(mock_redis)

    ignored_loggers = ["src.infrastructure.redis", "uvicorn", "fastapi", "asyncio"]

    for logger_name in ignored_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        try:
            logger.info(f"Should not be published from {logger_name}")
            await asyncio.sleep(0.01)
        finally:
            logger.removeHandler(handler)

    mock_redis.publish.assert_not_called()
