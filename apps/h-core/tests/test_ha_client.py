import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agents.electra.drivers.ha_client import HaClient

@pytest.mark.asyncio
async def test_ha_get_state_success():
    client = HaClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"entity_id": "light.living_room", "state": "on"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        state = await client.get_state("light.living_room")
        
        assert state["state"] == "on"
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_ha_call_service_success():
    client = HaClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        success = await client.call_service("light", "turn_on", {"entity_id": "light.kitchen"})
        
        assert success is True
        mock_post.assert_called_once()
