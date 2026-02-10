from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.visual.dreamer import Dreamer


@pytest.fixture
def mock_ha():
    ha = MagicMock()
    ha.get_state = AsyncMock()
    return ha


@pytest.fixture
def mock_visual_service():
    vs = MagicMock()
    vs.generate_and_index = AsyncMock(return_value="file:///media/generated/img.png")
    return vs


@pytest.mark.asyncio
async def test_dreamer_prepare_assets(mock_ha, mock_visual_service):
    # Mock HA responses
    mock_ha.get_state.side_effect = [
        {"state": "sunny"},  # weather.home
        {"state": "above_horizon", "attributes": {"elevation": 45}},  # sun.sun
    ]

    dreamer = Dreamer(mock_ha, mock_visual_service)

    await dreamer.prepare_daily_assets()

    # Verify HA calls
    assert mock_ha.get_state.call_count == 2

    # Verify Visual Service call
    mock_visual_service.generate_and_index.assert_called_once()
    args = mock_visual_service.generate_and_index.call_args[1]
    assert "sunny" in args["prompt"]
    assert "daylight" in args["prompt"]
    assert "proactive" in args["tags"]


@pytest.mark.asyncio
async def test_dreamer_get_time_of_day_fallback(mock_ha, mock_visual_service):
    # Mock HA to return None for sun.sun
    mock_ha.get_state.return_value = None

    dreamer = Dreamer(mock_ha, mock_visual_service)

    # We can't easily mock datetime.now in the middle of a function without patch,
    # but we can check if it returns ONE of the valid fallback strings.
    time_of_day = await dreamer.get_time_of_day_context()
    assert time_of_day in ["dawn", "daylight", "sunset", "night"]
