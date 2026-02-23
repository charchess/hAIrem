import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_surreal():
    surreal = MagicMock()
    surreal.store_dream = AsyncMock()
    surreal.get_pending_dream = AsyncMock(return_value=None)
    surreal.mark_dream_consumed = AsyncMock()
    return surreal


@pytest.fixture
def mock_visual_service():
    svc = MagicMock()
    svc.generate_and_index = AsyncMock(return_value=("http://example.com/img.png", "visual_asset:abc123"))
    return svc


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.get_completion = AsyncMock(return_value="Ethereal neon-cyberpunk portrait, glowing circuits, nighttime")
    return llm


@pytest.fixture
def dreamer(mock_visual_service, mock_llm, mock_surreal):
    from src.services.visual.dreamer import Dreamer

    return Dreamer(
        ha_client=MagicMock(),
        visual_service=mock_visual_service,
        llm_client=mock_llm,
        surreal_client=mock_surreal,
    )


@pytest.mark.asyncio
async def test_generate_creative_impulse_calls_llm(dreamer, mock_llm):
    result = await dreamer.generate_creative_impulse("lisa", "A witty, sarcastic AI with cat-like energy")
    mock_llm.get_completion.assert_called_once()
    assert "Ethereal neon-cyberpunk" in result


@pytest.mark.asyncio
async def test_generate_creative_impulse_fallback_when_no_llm(mock_visual_service, mock_surreal):
    from src.services.visual.dreamer import Dreamer

    dreamer_no_llm = Dreamer(ha_client=MagicMock(), visual_service=mock_visual_service)
    result = await dreamer_no_llm.generate_creative_impulse("lisa", "A witty character")
    assert "lisa" in result.lower() or len(result) > 0


@pytest.mark.asyncio
async def test_prepare_daily_assets_stores_dream_per_agent(dreamer, mock_surreal, mock_visual_service):
    agents = [
        {"id": "lisa", "persona": "A witty sarcastic AI"},
        {"id": "rex", "persona": "A stoic guardian"},
    ]
    await dreamer.prepare_daily_assets(agents=agents)

    assert mock_visual_service.generate_and_index.call_count >= 2
    assert mock_surreal.store_dream.call_count == 2

    calls = [call.args for call in mock_surreal.store_dream.call_args_list]
    agent_ids = [c[0] for c in calls]
    assert "lisa" in agent_ids
    assert "rex" in agent_ids


@pytest.mark.asyncio
async def test_prepare_daily_assets_skips_dream_if_no_surreal(mock_visual_service, mock_llm):
    from src.services.visual.dreamer import Dreamer

    dreamer_no_surreal = Dreamer(
        ha_client=MagicMock(),
        visual_service=mock_visual_service,
        llm_client=mock_llm,
    )
    agents = [{"id": "lisa", "persona": "A witty AI"}]
    await dreamer_no_surreal.prepare_daily_assets(agents=agents)
    mock_visual_service.generate_and_index.assert_called()


@pytest.mark.asyncio
async def test_get_dream_context_returns_formatted_string(mock_surreal):
    mock_surreal.get_pending_dream.return_value = {
        "prompt": "Neon cyberpunk outfit with glowing circuits",
        "asset_id": "visual_asset:abc123",
    }

    from src.domain.agent import AgentContext

    agent = MagicMock()
    agent.surreal = mock_surreal
    agent.config = MagicMock()
    agent.config.name = "lisa"

    from src.domain.agent import BaseAgent

    result = await BaseAgent._get_dream_context(agent)

    assert "CREATIVE DREAM" in result
    assert "Neon cyberpunk" in result
    mock_surreal.mark_dream_consumed.assert_called_once_with("lisa")


@pytest.mark.asyncio
async def test_get_dream_context_returns_empty_when_no_pending(mock_surreal):
    mock_surreal.get_pending_dream.return_value = None

    agent = MagicMock()
    agent.surreal = mock_surreal
    agent.config = MagicMock()
    agent.config.name = "lisa"

    from src.domain.agent import BaseAgent

    result = await BaseAgent._get_dream_context(agent)

    assert result == ""
    mock_surreal.mark_dream_consumed.assert_not_called()


@pytest.mark.asyncio
async def test_get_dream_context_returns_empty_when_no_surreal():
    agent = MagicMock()
    agent.surreal = None

    from src.domain.agent import BaseAgent

    result = await BaseAgent._get_dream_context(agent)
    assert result == ""
