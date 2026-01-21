import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

@pytest.mark.asyncio
async def test_agent_initialization():
    config = AgentConfig(name="TestAgent", role="Tester")
    mock_redis = AsyncMock()
    agent = BaseAgent(config, mock_redis)
    
    assert agent.ctx.agent_id == "TestAgent"
    assert agent.system_prompt == "You are TestAgent, a Tester."

@pytest.mark.asyncio
async def test_agent_command_execution():
    config = AgentConfig(name="TestAgent", role="Tester")
    mock_redis = AsyncMock()
    agent = BaseAgent(config, mock_redis)
    
    # Mock a command handler
    async def mock_handler(payload):
        return "handled"
    
    agent.register_command("test_cmd", mock_handler)
    
    # Simulate receiving a command message
    incoming_msg = HLinkMessage(
        type=MessageType.EXPERT_COMMAND,
        sender=Sender(agent_id="Sender", role="User"),
        recipient=Recipient(target="TestAgent"),
        payload=Payload(content={"command": "test_cmd"})
    )
    
    await agent.on_message(incoming_msg)
    
    # Verify response was sent
    mock_redis.publish.assert_called_once()
    call_args = mock_redis.publish.call_args
    channel = call_args[0][0]
    msg_sent = call_args[0][1]
    
    assert channel == "agent:Sender"
    assert msg_sent.type == MessageType.EXPERT_RESPONSE
    assert msg_sent.payload.content["result"] == "handled"
