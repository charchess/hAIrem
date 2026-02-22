from __future__ import annotations
from typing import Any


async def get_current_weather(weather_entity: str = "weather.home", ha_client: Any = None, **kwargs) -> str:
    if ha_client is None:
        return "HA client unavailable — cannot read weather"
    state = await ha_client.get_state(weather_entity)
    return f"Current weather: {state}"


async def get_forecast(weather_entity: str = "weather.home", days: int = 3, ha_client: Any = None, **kwargs) -> str:
    if ha_client is None:
        return "HA client unavailable — cannot read forecast"
    state = await ha_client.get_state(weather_entity)
    return f"{days}-day forecast from {weather_entity}: {state}"
