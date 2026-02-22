import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestHaClientDiscovery:
    async def test_get_all_entities_returns_fetched_states(self):
        from src.infrastructure.ha_client import HaClient

        client = HaClient()
        fake_entities = [
            {"entity_id": "light.salon", "state": "on", "attributes": {}, "last_updated": "2026-01-01"},
            {"entity_id": "switch.bureau", "state": "off", "attributes": {}, "last_updated": "2026-01-01"},
        ]
        client.fetch_all_states = AsyncMock(return_value=fake_entities)

        result = await client.get_all_entities()

        assert result == fake_entities

    async def test_get_all_entities_caches_in_surrealdb(self):
        from src.infrastructure.ha_client import HaClient

        client = HaClient()
        fake_entities = [
            {"entity_id": "light.salon", "state": "on", "attributes": {}, "last_updated": "2026-01-01"},
        ]
        client.fetch_all_states = AsyncMock(return_value=fake_entities)

        surreal = MagicMock()
        surreal._call = AsyncMock()

        await client.get_all_entities(surreal=surreal)

        surreal._call.assert_called_once()
        call_args = surreal._call.call_args
        assert call_args[0][0] == "query"
        assert "ha_entities" in call_args[0][1]

    async def test_get_all_entities_no_surreal_still_returns_entities(self):
        from src.infrastructure.ha_client import HaClient

        client = HaClient()
        fake_entities = [{"entity_id": "sensor.temperature", "state": "21", "attributes": {}, "last_updated": ""}]
        client.fetch_all_states = AsyncMock(return_value=fake_entities)

        result = await client.get_all_entities(surreal=None)

        assert result == fake_entities

    async def test_get_all_entities_empty_when_no_token(self):
        from src.infrastructure.ha_client import HaClient

        with patch.dict("os.environ", {"HA_TOKEN": "", "HA_URL": "http://localhost/api"}):
            client = HaClient()
            client.token = None
            result = await client.get_all_entities()
            assert result == []

    async def test_get_all_entities_surrealdb_failure_is_non_blocking(self):
        from src.infrastructure.ha_client import HaClient

        client = HaClient()
        fake_entities = [{"entity_id": "light.test", "state": "on", "attributes": {}, "last_updated": ""}]
        client.fetch_all_states = AsyncMock(return_value=fake_entities)

        surreal = MagicMock()
        surreal._call = AsyncMock(side_effect=Exception("DB down"))

        result = await client.get_all_entities(surreal=surreal)

        assert result == fake_entities

    async def test_get_all_entities_passes_correct_fields_to_surreal(self):
        from src.infrastructure.ha_client import HaClient

        client = HaClient()
        fake_entities = [
            {
                "entity_id": "climate.salon",
                "state": "heat",
                "attributes": {"temperature": 21},
                "last_updated": "2026-02-01T10:00:00Z",
            }
        ]
        client.fetch_all_states = AsyncMock(return_value=fake_entities)

        surreal = MagicMock()
        surreal._call = AsyncMock()

        await client.get_all_entities(surreal=surreal)

        batch = surreal._call.call_args[0][2]["batch"]
        assert batch[0]["entity_id"] == "climate.salon"
        assert batch[0]["state"] == "heat"
        assert batch[0]["attributes"] == {"temperature": 21}
