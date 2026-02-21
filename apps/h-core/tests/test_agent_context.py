import pytest
from unittest.mock import AsyncMock
from src.domain.agent import BaseAgent, AgentContext
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload


@pytest.fixture
def mock_agent():
    config = AgentConfig(name="TestAgent", role="Tester", prompt="You are a test agent.")
    mock_redis = AsyncMock()
    mock_llm = AsyncMock()
    return BaseAgent(config, mock_redis, mock_llm)


@pytest.mark.asyncio
async def test_assemble_payload_structure(mock_agent):
    # 1. Setup history
    msg1 = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="User", role="user"),
        recipient=Recipient(target="TestAgent"),
        payload=Payload(content="Hello"),
    )
    msg2 = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="TestAgent", role="Tester"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="Hi there"),
    )
    mock_agent.ctx.history = [msg1, msg2]

    # 2. Current message
    current_msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="User", role="user"),
        recipient=Recipient(target="TestAgent"),
        payload=Payload(content="How are you?"),
    )

    # 3. Assemble
    payload = await mock_agent._assemble_payload(current_msg)

    # 4. Verify
    assert len(payload) == 4
    assert "You are a test agent." in payload[0]["content"]
    assert payload[1] == {"role": "user", "content": "Hello"}
    assert payload[2] == {"role": "assistant", "content": "Hi there"}
    assert payload[3] == {"role": "user", "content": "How are you?"}


@pytest.mark.asyncio
async def test_history_limit(mock_agent):
    # Add 15 messages
    for i in range(15):
        msg = HLinkMessage(
            type=MessageType.NARRATIVE_TEXT,
            sender=Sender(agent_id="User", role="user"),
            recipient=Recipient(target="TestAgent"),
            payload=Payload(content=f"Msg {i}"),
        )
        mock_agent.ctx.history.append(msg)

    current_msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="User", role="user"),
        recipient=Recipient(target="TestAgent"),
        payload=Payload(content="Last one"),
    )

    payload = await mock_agent._assemble_payload(current_msg)

    # System + 10 history + 1 current = 12
    assert len(payload) == 12
    # First history message should be Msg 5 (15-10)
    assert payload[1]["content"] == "Msg 5"
