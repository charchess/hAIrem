from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender
from src.services.chat.commands import CommandHandler


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.publish = AsyncMock()
    return redis


@pytest.fixture
def mock_visual():
    visual = MagicMock()
    visual.generate_and_index = AsyncMock(return_value=("file:///media/generated/test.png", "asset-123"))
    return visual


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    return llm


@pytest.mark.asyncio
async def test_agent_generate_image_tool(mock_redis, mock_visual, mock_llm):
    config = AgentConfig(
        name="test-agent",
        role="tester",
        skills=[{"name": "generate_image", "description": "Génère une image à partir d'un prompt textuel."}],
    )
    agent = BaseAgent(config, mock_redis, mock_llm, visual_service=mock_visual)

    # Check if tool is registered
    assert "generate_image" in agent.tools

    # Execute tool
    result = await agent.generate_image(prompt="a test image", style="cinematic")

    assert "Image successfully generated" in result
    mock_visual.generate_and_index.assert_called_once_with(
        agent_id="test-agent", prompt="a test image", style_preset="cinematic"
    )


@pytest.mark.asyncio
async def test_command_handler_imagine(mock_redis, mock_visual):
    handler = CommandHandler(mock_redis, mock_visual)

    msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="/imagine a beautiful landscape"),
    )

    # Execute command
    handled = await handler.execute("/imagine a beautiful landscape", msg)

    assert handled is True
    # Verify immediate response
    assert mock_redis.publish.call_count >= 1
    call_args = mock_redis.publish.call_args_list[0]
    assert call_args[0][0] == "broadcast"
    response_msg = call_args[0][1]
    assert "J'imagine" in response_msg.payload.content

    # Give some time for the background task
    import asyncio

    await asyncio.sleep(0.1)

    # Verify visual service call
    mock_visual.generate_and_index.assert_called_once_with(
        agent_id="system",
        prompt="a beautiful landscape",
        tags=["user_requested", "slash_command"],
        asset_type="background",
    )
