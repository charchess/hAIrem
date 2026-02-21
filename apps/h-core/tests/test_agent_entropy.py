import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../agents")))

from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload


def make_entropy_agent():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "entropy_logic",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../agents/entropy/logic.py")),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    config = AgentConfig(name="Dieu", role="Entropie Narrative", personified=False)
    redis = AsyncMock()
    redis.publish = AsyncMock()
    llm = AsyncMock()
    llm.model = "mock"
    llm.cache = None
    llm.get_completion = AsyncMock(return_value="ok")
    llm.get_embedding = AsyncMock(return_value=[0.0] * 768)

    surreal = AsyncMock()
    surreal.get_config = AsyncMock(return_value=None)

    agent = module.Agent(config=config, redis_client=redis, llm_client=llm, surreal_client=surreal)
    return agent, redis


@pytest.mark.asyncio
async def test_entropy_whispers_on_inactivity():
    agent, redis = make_entropy_agent()

    msg = HLinkMessage(
        type=MessageType.SYSTEM_INACTIVITY,
        sender=Sender(agent_id="core", role="system"),
        recipient=Recipient(target="Dieu"),
        payload=Payload(content="inactivity"),
    )

    await agent.on_message(msg)

    redis.publish.assert_called_once()
    call_args = redis.publish.call_args[0]
    published_msg = call_args[1]
    assert published_msg.type == MessageType.SYSTEM_WHISPER


@pytest.mark.asyncio
async def test_entropy_ignores_user_narrative():
    agent, redis = make_entropy_agent()

    msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="Bonjour !"),
    )

    await agent.on_message(msg)

    redis.publish.assert_not_called()
    assert len(agent.ctx.history) == 1


@pytest.mark.asyncio
async def test_entropy_uses_registry_targets_when_available():
    agent, redis = make_entropy_agent()

    mock_registry = MagicMock()
    renarde_mock = MagicMock()
    renarde_mock.is_active = True
    lisa_mock = MagicMock()
    lisa_mock.is_active = True
    mock_registry.agents = {"Renarde": renarde_mock, "lisa": lisa_mock, "Dieu": MagicMock(is_active=True)}
    agent.registry = mock_registry

    await agent._trigger_spark()

    redis.publish.assert_called_once()
    channel = redis.publish.call_args[0][0]
    assert channel in ("agent:Renarde", "agent:lisa")
