import pytest
import asyncio
import os
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig
from src.main import RedisLogHandler
from src.models.hlink import MessageType, HLinkMessage, Sender, Recipient, Payload


@pytest.fixture
def mock_agent():
    config = AgentConfig(name="Lisa", role="Developer")
    redis = AsyncMock()
    llm = AsyncMock()
    return BaseAgent(config, redis, llm)


def test_addressing_check(mock_agent):
    # Case 1: No addressing
    assert mock_agent._check_addressing("Hello everyone") is False

    # Case 2: Addressed to me (@)
    assert mock_agent._check_addressing("@Lisa hello") is True

    # Case 3: Addressed to someone else (@)
    assert mock_agent._check_addressing("@Electra hello") is False

    # Case 4: Addressed to me (comma)
    assert mock_agent._check_addressing("Lisa, hello") is True

    # Case 5: Addressed to someone else (comma)
    assert mock_agent._check_addressing("Electra, hello") is False

    # Case 6: Mixed / Natural
    assert mock_agent._check_addressing("Hey @Lisa, check this") is True
    # assert mock_agent._check_addressing("Bonjour a Lisa") is True
    assert mock_agent._check_addressing("Dis moi Renarde, ça va ?") is False  # Mentions Renarde, not Lisa
    assert (
        mock_agent._check_addressing("Salut Lisa et Renarde") is True
    )  # Mentions both, both should respond? Yes for now.


@pytest.mark.asyncio
async def test_log_level_filtering():
    mock_redis = AsyncMock()
    handler = RedisLogHandler(mock_redis)
    handler.setFormatter(logging.Formatter("%(message)s"))

    # Set log level to ERROR
    handler.setLevel("ERROR")

    # Mock loop to be running
    handler.loop = MagicMock()
    handler.loop.is_running.return_value = True

    # Info log should be ignored
    record_info = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0, msg="Info message", args=(), exc_info=None
    )
    handler.emit(record_info)
    await asyncio.sleep(0.01)
    mock_redis.publish.assert_not_called()

    # Error log should be published
    record_error = logging.LogRecord(
        name="test", level=logging.ERROR, pathname="", lineno=0, msg="Error message", args=(), exc_info=None
    )
    handler.emit(record_error)

    # We need to wait for the task
    for _ in range(10):
        if mock_redis.publish_event.called:
            break
        await asyncio.sleep(0.1)  # Increased wait time

    mock_redis.publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_internal_broadcast_logic(mock_agent):
    # Verify send_internal_note publishes to broadcast channel
    await mock_agent.send_internal_note("broadcast", "System alert")

    mock_agent.redis.publish.assert_called_once()
    args, kwargs = mock_agent.redis.publish.call_args
    assert args[0] == "broadcast"
    msg = args[1]
    assert msg.type == MessageType.AGENT_INTERNAL_NOTE
    assert msg.recipient.target == "broadcast"
