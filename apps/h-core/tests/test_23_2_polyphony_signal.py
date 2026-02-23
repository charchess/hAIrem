import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from src.models.hlink import MessageType, HLinkMessage, Sender, Recipient, Payload


def _make_agent():
    from src.domain.agent import BaseAgent
    from src.models.agent import AgentConfig

    config = AgentConfig(name="lisa", role="companion", prompt="You are Lisa.")
    mock_redis = MagicMock()
    mock_redis.publish_event = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_redis.xadd = AsyncMock()
    mock_llm = MagicMock()
    mock_llm.model = "test"
    mock_llm.cache = None
    agent = BaseAgent(config=config, redis_client=mock_redis, llm_client=mock_llm)
    return agent, mock_redis


def _make_trigger():
    return HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="lisa"),
        payload=Payload(content="Salut !"),
    )


@pytest.mark.asyncio
async def test_speaking_signal_published_on_start():
    agent, mock_redis = _make_agent()
    trigger = _make_trigger()

    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock(message=MagicMock(content="Bonjour !"))]
    agent.llm.get_completion = AsyncMock(return_value=mock_llm_response)
    agent.llm.get_usage_from_response = MagicMock(
        return_value={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    )
    agent.llm.get_model_provider = MagicMock(return_value=("openai", "gpt-4"))
    agent._assemble_payload = AsyncMock(return_value=[])

    await agent.generate_response(trigger)

    calls = mock_redis.publish_event.call_args_list
    speaking_calls = [
        c
        for c in calls
        if c[0][0] == "system_stream"
        and c[0][1].get("type") == MessageType.AGENT_SPEAKING
        and c[0][1]["payload"]["content"].get("speaking") is True
    ]
    assert len(speaking_calls) >= 1, "speaking=True signal must be published at start"


@pytest.mark.asyncio
async def test_idle_signal_published_on_response_end():
    agent, mock_redis = _make_agent()
    trigger = _make_trigger()

    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock(message=MagicMock(content="Bonjour !"))]
    agent.llm.get_completion = AsyncMock(return_value=mock_llm_response)
    agent.llm.get_usage_from_response = MagicMock(
        return_value={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    )
    agent.llm.get_model_provider = MagicMock(return_value=("openai", "gpt-4"))
    agent._assemble_payload = AsyncMock(return_value=[])

    await agent.generate_response(trigger)

    calls = mock_redis.publish_event.call_args_list
    idle_calls = [
        c
        for c in calls
        if c[0][0] == "system_stream"
        and c[0][1].get("type") == MessageType.AGENT_SPEAKING
        and c[0][1]["payload"]["content"].get("speaking") is False
    ]
    assert len(idle_calls) >= 1, "speaking=False (idle) signal must be published after response"


@pytest.mark.asyncio
async def test_idle_signal_published_even_on_llm_error():
    agent, mock_redis = _make_agent()
    trigger = _make_trigger()

    agent.llm.get_completion = AsyncMock(side_effect=Exception("LLM exploded"))
    agent._assemble_payload = AsyncMock(return_value=[])

    await agent.generate_response(trigger)

    calls = mock_redis.publish_event.call_args_list
    idle_calls = [
        c
        for c in calls
        if c[0][0] == "system_stream"
        and c[0][1].get("type") == MessageType.AGENT_SPEAKING
        and c[0][1]["payload"]["content"].get("speaking") is False
    ]
    assert len(idle_calls) >= 1, "idle signal must be published even when LLM raises"


@pytest.mark.asyncio
async def test_speaking_signal_contains_agent_id():
    agent, mock_redis = _make_agent()
    trigger = _make_trigger()

    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock(message=MagicMock(content="Hello"))]
    agent.llm.get_completion = AsyncMock(return_value=mock_llm_response)
    agent.llm.get_usage_from_response = MagicMock(
        return_value={"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}
    )
    agent.llm.get_model_provider = MagicMock(return_value=("openai", "gpt-4"))
    agent._assemble_payload = AsyncMock(return_value=[])

    await agent.generate_response(trigger)

    calls = mock_redis.publish_event.call_args_list
    for c in calls:
        if c[0][1].get("type") == MessageType.AGENT_SPEAKING:
            assert c[0][1]["sender"]["agent_id"] == "lisa"
            break
    else:
        pytest.fail("No AGENT_SPEAKING signal found")


@pytest.mark.asyncio
async def test_idle_signal_published_after_speaking_signal():
    agent, mock_redis = _make_agent()
    trigger = _make_trigger()

    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock(message=MagicMock(content="Hello"))]
    agent.llm.get_completion = AsyncMock(return_value=mock_llm_response)
    agent.llm.get_usage_from_response = MagicMock(
        return_value={"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}
    )
    agent.llm.get_model_provider = MagicMock(return_value=("openai", "gpt-4"))
    agent._assemble_payload = AsyncMock(return_value=[])

    await agent.generate_response(trigger)

    calls = mock_redis.publish_event.call_args_list
    speaking_events = [
        (i, c[0][1]["payload"]["content"].get("speaking"))
        for i, c in enumerate(calls)
        if c[0][1].get("type") == MessageType.AGENT_SPEAKING
    ]

    assert len(speaking_events) >= 2, "Must publish both speaking=True and speaking=False"
    first_idx = next(i for i, s in speaking_events if s is True)
    last_idx = next(i for i, s in reversed(speaking_events) if s is False)
    assert first_idx < last_idx, "speaking=True must come before speaking=False"
