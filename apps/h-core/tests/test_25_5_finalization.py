import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from src.services.visual.service import VisualImaginationService
from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender

@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.publish = AsyncMock()
    return redis

@pytest.fixture
def mock_visual_provider():
    provider = MagicMock()
    provider.generate = AsyncMock(return_value="http://example.com/image.png")
    return provider

@pytest.fixture
def mock_asset_manager():
    manager = MagicMock()
    manager.get_asset_by_prompt = AsyncMock(return_value=None)
    manager.save_asset = AsyncMock(return_value="file:///tmp/test.png")
    return manager

@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.get_embedding = AsyncMock(return_value=[0.1]*1536)
    llm.get_completion = AsyncMock()
    return llm

@pytest.fixture
def mock_surreal():
    surreal = MagicMock()
    surreal.get_agent_state = AsyncMock(return_value=[
        {"relation": "WEARS", "name": "red_dress", "description": "A beautiful red dress"},
        {"relation": "IS_IN", "name": "beach", "description": "The sunny beach"}
    ])
    return surreal

@pytest.mark.asyncio
async def test_visual_raw_prompt_broadcast(mock_redis, mock_visual_provider, mock_asset_manager, mock_llm):
    service = VisualImaginationService(
        visual_provider=mock_visual_provider,
        asset_manager=mock_asset_manager,
        llm_client=mock_llm,
        redis_client=mock_redis
    )
    
    # Mock bible to return some prompt parts
    from src.services.visual.bible import bible
    bible.get_character_desc = MagicMock(return_value="A cute girl")
    
    await service.generate_for_agent(agent_id="lisa", prompt="smiling at the beach")
    
    # Verify Redis broadcast of raw prompt
    broadcast_calls = [call for call in mock_redis.publish.call_args_list if call[0][1].type == MessageType.VISUAL_RAW_PROMPT]
    assert len(broadcast_calls) == 1
    msg = broadcast_calls[0][0][1]
    assert msg.payload.content["agent_id"] == "lisa"
    assert "smiling at the beach" in msg.payload.content["prompt"]

@pytest.mark.asyncio
async def test_burning_memory_injection(mock_redis, mock_llm, mock_surreal):
    config = AgentConfig(name="lisa", role="companion")
    agent = BaseAgent(config, mock_redis, mock_llm, surreal_client=mock_surreal)
    
    msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="lisa"),
        payload=Payload(content="Hello Lisa, where are you?")
    )
    
    payload = await agent._assemble_payload(msg)
    
    # Check if system prompt contains burning memory
    system_msg = next(m for m in payload if m["role"] == "system")
    assert "CURRENTLY WEARING: A beautiful red dress" in system_msg["content"]
    assert "CURRENT LOCATION: beach" in system_msg["content"]
    assert "### LIVE FACTS (OBJECTIVE REALITY) ###" in system_msg["content"]
