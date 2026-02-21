import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import logging
import os

import pytest
pytestmark = pytest.mark.integration


# Mock infrastructure before importing main to avoid side effects
with patch("src.infrastructure.redis.RedisClient"), \
     patch("src.infrastructure.surrealdb.SurrealDbClient"), \
     patch("src.infrastructure.llm.LlmClient"), \
     patch("src.infrastructure.plugin_loader.PluginLoader"):
    from src.main import RedisLogHandler
    from src.utils.privacy import PrivacyFilter
    privacy_filter = PrivacyFilter()

@pytest.mark.asyncio
async def test_redis_log_handler_publishes_to_redis():
    """Test that RedisLogHandler publishes log messages to Redis."""
    mock_redis = MagicMock()
    mock_redis.publish_event = AsyncMock()
    
    handler = RedisLogHandler(mock_redis)
    handler.log_level = "INFO"
    
    # Create a log record
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test log message",
        args=(),
        exc_info=None
    )
    
    # Emit will trigger an async task
    handler.emit(record)
    
    # Give it a moment to process the task
    await asyncio.sleep(0.1)
    
    # Verify that the message was published to Redis
    assert mock_redis.publish_event.called

@pytest.mark.asyncio
async def test_message_persistence_redaction_logic():
    from src.models.hlink import HLinkMessage, Sender, Recipient, MessageType
    from uuid import uuid4
    
    hlink_msg = HLinkMessage(
        id=uuid4(),
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="Lisa"),
        payload={"content": "My password: supersecret123"}
    )
    
    # Apply redaction logic as implemented in main.py
    msg_data = hlink_msg.model_dump()
    if isinstance(msg_data.get("payload", {}).get("content"), str):
        redacted_text, _ = privacy_filter.redact(msg_data["payload"]["content"])
        msg_data["payload"]["content"] = redacted_text
    
    # Verify
    assert "supersecret123" not in msg_data["payload"]["content"]
    assert "[REDACTED]" in msg_data["payload"]["content"]
