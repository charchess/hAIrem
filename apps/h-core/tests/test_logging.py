import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, patch, MagicMock
from src.models.hlink import MessageType
from src.main import RedisLogHandler


@pytest.mark.asyncio
async def test_redis_log_handler_publishes_to_redis():
    mock_redis = AsyncMock()
    handler = RedisLogHandler(mock_redis)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Mock loop
    handler.loop = MagicMock()
    handler.loop.is_running.return_value = True

    try:
        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value = asyncio.get_event_loop()
            logger.info("Test message")

            # Give some time for the task to be created and executed
            await asyncio.sleep(0.1)

        mock_redis.publish_event.assert_called_once()
        args, kwargs = mock_redis.publish_event.call_args
        assert args[0] == "system_stream"
        message_data = args[1]
        assert message_data["type"] == "system.log"
        assert "INFO:Test message" in message_data["payload"]["content"]
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
