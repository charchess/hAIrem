import pytest
from unittest.mock import AsyncMock


class TestMusicSkill:
    @pytest.mark.asyncio
    async def test_play_music_no_ha_client_returns_message(self):
        from src.skills.music import play_music

        result = await play_music("media_player.salon")
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_play_music_with_ha_client_calls_service(self):
        from src.skills.music import play_music

        ha = AsyncMock()
        result = await play_music("media_player.salon", media_content_id="spotify:track:123", ha_client=ha)
        ha.call_service.assert_called_once()
        assert "salon" in result

    @pytest.mark.asyncio
    async def test_pause_music_no_ha_client(self):
        from src.skills.music import pause_music

        result = await pause_music("media_player.salon")
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_pause_music_with_ha_client(self):
        from src.skills.music import pause_music

        ha = AsyncMock()
        result = await pause_music("media_player.salon", ha_client=ha)
        ha.call_service.assert_called_once()
        assert "salon" in result.lower()

    @pytest.mark.asyncio
    async def test_set_volume_no_ha_client(self):
        from src.skills.music import set_volume

        result = await set_volume("media_player.salon", 0.5)
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_set_volume_clamps_and_calls_service(self):
        from src.skills.music import set_volume

        ha = AsyncMock()
        result = await set_volume("media_player.salon", 1.5, ha_client=ha)
        ha.call_service.assert_called_once()
        call_args = ha.call_service.call_args[0]
        assert call_args[2]["volume_level"] == 1.0

    @pytest.mark.asyncio
    async def test_set_volume_clamps_below_zero(self):
        from src.skills.music import set_volume

        ha = AsyncMock()
        await set_volume("media_player.salon", -0.5, ha_client=ha)
        call_args = ha.call_service.call_args[0]
        assert call_args[2]["volume_level"] == 0.0


class TestCalendarSkill:
    @pytest.mark.asyncio
    async def test_get_events_no_ha_client(self):
        from src.skills.calendar import get_events

        result = await get_events("calendar.home")
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_get_events_with_ha_client(self):
        from src.skills.calendar import get_events

        ha = AsyncMock()
        ha.get_state.return_value = {"events": []}
        result = await get_events("calendar.home", ha_client=ha)
        ha.get_state.assert_called_once_with("calendar.home")

    @pytest.mark.asyncio
    async def test_create_event_no_ha_client(self):
        from src.skills.calendar import create_event

        result = await create_event("calendar.home", "Meeting", "2024-01-01T09:00", "2024-01-01T10:00")
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_create_event_with_ha_client(self):
        from src.skills.calendar import create_event

        ha = AsyncMock()
        result = await create_event("calendar.home", "Meeting", "2024-01-01T09:00", "2024-01-01T10:00", ha_client=ha)
        ha.call_service.assert_called_once()
        assert "Meeting" in result


class TestCookingSkill:
    @pytest.mark.asyncio
    async def test_suggest_recipe_with_ingredients(self):
        from src.skills.cooking import suggest_recipe

        result = await suggest_recipe(["tomato", "pasta"])
        assert "tomato" in result or "pasta" in result

    @pytest.mark.asyncio
    async def test_suggest_recipe_empty_ingredients(self):
        from src.skills.cooking import suggest_recipe

        result = await suggest_recipe([])
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_substitute_ingredient_known(self):
        from src.skills.cooking import substitute_ingredient

        result = await substitute_ingredient("butter")
        assert "oil" in result.lower()

    @pytest.mark.asyncio
    async def test_substitute_ingredient_unknown(self):
        from src.skills.cooking import substitute_ingredient

        result = await substitute_ingredient("truffle")
        assert "No known substitution" in result

    @pytest.mark.asyncio
    async def test_set_timer_no_ha_client_simulation(self):
        from src.skills.cooking import set_timer

        result = await set_timer(10, "pasta")
        assert "10" in result or "Timer" in result

    @pytest.mark.asyncio
    async def test_set_timer_with_ha_client(self):
        from src.skills.cooking import set_timer

        ha = AsyncMock()
        result = await set_timer(5, "sauce", ha_client=ha)
        ha.call_service.assert_called_once()
        assert "5" in result


class TestHomeAssistantSkill:
    @pytest.mark.asyncio
    async def test_turn_on_no_ha_client(self):
        from src.skills.home_assistant import turn_on

        result = await turn_on("light.salon")
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_turn_on_with_ha_client(self):
        from src.skills.home_assistant import turn_on

        ha = AsyncMock()
        result = await turn_on("light.salon", ha_client=ha)
        ha.call_service.assert_called_once_with("homeassistant", "turn_on", {"entity_id": "light.salon"})
        assert "light.salon" in result

    @pytest.mark.asyncio
    async def test_turn_off_no_ha_client(self):
        from src.skills.home_assistant import turn_off

        result = await turn_off("light.salon")
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_turn_off_with_ha_client(self):
        from src.skills.home_assistant import turn_off

        ha = AsyncMock()
        result = await turn_off("light.salon", ha_client=ha)
        ha.call_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_state_no_ha_client(self):
        from src.skills.home_assistant import get_state

        result = await get_state("sensor.temp")
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_get_state_with_ha_client(self):
        from src.skills.home_assistant import get_state

        ha = AsyncMock()
        ha.get_state.return_value = "22.5"
        result = await get_state("sensor.temp", ha_client=ha)
        assert "22.5" in result

    @pytest.mark.asyncio
    async def test_set_temperature_no_ha_client(self):
        from src.skills.home_assistant import set_temperature

        result = await set_temperature("climate.salon", 21.0)
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_set_temperature_with_ha_client(self):
        from src.skills.home_assistant import set_temperature

        ha = AsyncMock()
        result = await set_temperature("climate.salon", 21.0, ha_client=ha)
        ha.call_service.assert_called_once()
        assert "21" in result


class TestWeatherSkill:
    @pytest.mark.asyncio
    async def test_get_current_weather_no_ha_client(self):
        from src.skills.weather import get_current_weather

        result = await get_current_weather()
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_get_current_weather_with_ha_client(self):
        from src.skills.weather import get_current_weather

        ha = AsyncMock()
        ha.get_state.return_value = "sunny, 24°C"
        result = await get_current_weather(ha_client=ha)
        assert "sunny" in result

    @pytest.mark.asyncio
    async def test_get_forecast_no_ha_client(self):
        from src.skills.weather import get_forecast

        result = await get_forecast()
        assert "unavailable" in result

    @pytest.mark.asyncio
    async def test_get_forecast_with_ha_client(self):
        from src.skills.weather import get_forecast

        ha = AsyncMock()
        ha.get_state.return_value = "mixed"
        result = await get_forecast(days=5, ha_client=ha)
        assert "5" in result
        assert "forecast" in result.lower()
