import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.chat.commands import CommandHandler
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender

@pytest.mark.asyncio
async def test_run_outfit_integration():
    redis = AsyncMock()
    visual = AsyncMock()
    surreal = AsyncMock()
    
    handler = CommandHandler(redis, visual, surreal)
    
    msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="/outfit lisa a sparkly blue dress")
    )
    
    # Execute command
    await handler.execute("/outfit lisa a sparkly blue dress", msg)
    
    # 1. Verify surreal.update_agent_state was called
    surreal.update_agent_state.assert_called_once()
    args = surreal.update_agent_state.call_args[0]
    assert args[0] == "lisa"
    assert args[1] == "WEARS"
    assert "sparkly blue dress" in args[2]["description"]
    
    # 2. Verify notification was published to redis
    # Should have 2 publishes: 1 for ACK, 1 for Agent Notification
    # Actually _send_ack is also called.
    
    # Filter for the notification message
    notifications = [call[0][1] for call in redis.publish.call_args_list if isinstance(call[0][1], HLinkMessage) and call[0][1].recipient.target == "lisa"]
    assert len(notifications) == 1
    assert "Your state updated" in notifications[0].payload.content
    
    # 3. Verify visual generation was triggered
    visual.generate_and_index.assert_called_once()
    v_args = visual.generate_and_index.call_args[1]
    assert v_args["agent_id"] == "lisa"
    assert "sparkly blue dress" in v_args["prompt"]

@pytest.mark.asyncio
async def test_run_location_integration():
    redis = AsyncMock()
    visual = AsyncMock()
    surreal = AsyncMock()
    
    handler = CommandHandler(redis, visual, surreal)
    
    msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="/location lisa the garden")
    )
    
    await handler.execute("/location lisa the garden", msg)
    
    surreal.update_agent_state.assert_called_once()
    args = surreal.update_agent_state.call_args[0]
    assert args[0] == "lisa"
    assert args[1] == "IS_IN"
    assert args[2]["name"] == "the garden"
    
    notifications = [call[0][1] for call in redis.publish.call_args_list if isinstance(call[0][1], HLinkMessage) and call[0][1].recipient.target == "lisa"]
    assert len(notifications) == 1
    assert "You are now in 'the garden'" in notifications[0].payload.content
