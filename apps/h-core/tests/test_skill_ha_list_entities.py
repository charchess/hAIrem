import pytest
from unittest.mock import AsyncMock, MagicMock

pytestmark = pytest.mark.asyncio


class TestListEntitiesSkill:
    async def test_list_entities_returns_formatted_string(self):
        from src.skills.home_assistant import list_entities

        mock_ha = MagicMock()
        mock_ha.get_all_entities = AsyncMock(
            return_value=[
                {"entity_id": "light.salon", "state": "on", "attributes": {}, "last_updated": "2026-01-01"},
                {"entity_id": "switch.bureau", "state": "off", "attributes": {}, "last_updated": "2026-01-01"},
            ]
        )

        result = await list_entities(ha_client=mock_ha)

        assert "light.salon" in result
        assert "switch.bureau" in result
        assert isinstance(result, str)

    async def test_list_entities_filters_by_domain(self):
        from src.skills.home_assistant import list_entities

        mock_ha = MagicMock()
        mock_ha.get_all_entities = AsyncMock(
            return_value=[
                {"entity_id": "light.salon", "state": "on", "attributes": {}, "last_updated": "2026-01-01"},
                {"entity_id": "light.chambre", "state": "off", "attributes": {}, "last_updated": "2026-01-01"},
                {"entity_id": "switch.bureau", "state": "on", "attributes": {}, "last_updated": "2026-01-01"},
            ]
        )

        result = await list_entities(ha_client=mock_ha, domain_filter="light")

        assert "light.salon" in result
        assert "light.chambre" in result
        assert "switch.bureau" not in result

    async def test_list_entities_returns_graceful_error_when_no_client(self):
        from src.skills.home_assistant import list_entities

        result = await list_entities(ha_client=None)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "unavailable" in result.lower() or "ha" in result.lower() or "client" in result.lower()

    async def test_list_entities_passes_surreal_to_get_all_entities(self):
        from src.skills.home_assistant import list_entities

        mock_ha = MagicMock()
        mock_ha.get_all_entities = AsyncMock(return_value=[])
        mock_surreal = MagicMock()

        await list_entities(ha_client=mock_ha, surreal_client=mock_surreal)

        mock_ha.get_all_entities.assert_called_once_with(surreal=mock_surreal)

    async def test_list_entities_includes_state_in_output(self):
        from src.skills.home_assistant import list_entities

        mock_ha = MagicMock()
        mock_ha.get_all_entities = AsyncMock(
            return_value=[
                {"entity_id": "light.salon", "state": "on", "attributes": {}, "last_updated": "2026-01-01"},
            ]
        )

        result = await list_entities(ha_client=mock_ha)

        assert "on" in result

    async def test_list_entities_empty_returns_informative_message(self):
        from src.skills.home_assistant import list_entities

        mock_ha = MagicMock()
        mock_ha.get_all_entities = AsyncMock(return_value=[])

        result = await list_entities(ha_client=mock_ha)

        assert isinstance(result, str)
        assert len(result) > 0

    async def test_list_entities_domain_filter_no_match_returns_informative_message(self):
        from src.skills.home_assistant import list_entities

        mock_ha = MagicMock()
        mock_ha.get_all_entities = AsyncMock(
            return_value=[
                {"entity_id": "light.salon", "state": "on", "attributes": {}, "last_updated": "2026-01-01"},
            ]
        )

        result = await list_entities(ha_client=mock_ha, domain_filter="climate")

        assert isinstance(result, str)
        assert "climate" in result or "no" in result.lower() or "0" in result
