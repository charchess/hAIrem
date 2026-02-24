from __future__ import annotations
from typing import Any


async def list_entities(
    ha_client: Any = None,
    surreal_client: Any = None,
    domain_filter: str | None = None,
    **kwargs,
) -> str:
    if ha_client is None:
        return "HA client unavailable — cannot list entities"
    entities = await ha_client.get_all_entities(surreal=surreal_client)
    if domain_filter:
        entities = [e for e in entities if e.get("entity_id", "").startswith(f"{domain_filter}.")]
    if not entities:
        if domain_filter:
            return f"No entities found for domain: {domain_filter}"
        return "No entities found"
    lines = [f"{e['entity_id']}: {e.get('state', 'unknown')}" for e in entities]
    return "\n".join(lines)


async def turn_on(entity_id: str, ha_client: Any = None, **kwargs) -> str:
    if ha_client is None:
        return f"HA client unavailable — cannot turn on {entity_id}"
    await ha_client.call_service("homeassistant", "turn_on", {"entity_id": entity_id})
    return f"Turned on {entity_id}"


async def turn_off(entity_id: str, ha_client: Any = None, **kwargs) -> str:
    if ha_client is None:
        return f"HA client unavailable — cannot turn off {entity_id}"
    await ha_client.call_service("homeassistant", "turn_off", {"entity_id": entity_id})
    return f"Turned off {entity_id}"


async def get_state(entity_id: str, ha_client: Any = None, **kwargs) -> str:
    if ha_client is None:
        return f"HA client unavailable — cannot read state of {entity_id}"
    state = await ha_client.get_state(entity_id)
    return str(state)


async def set_temperature(entity_id: str, temperature: float, ha_client: Any = None, **kwargs) -> str:
    if ha_client is None:
        return f"HA client unavailable — cannot set temperature on {entity_id}"
    await ha_client.call_service("climate", "set_temperature", {"entity_id": entity_id, "temperature": temperature})
    return f"Set {entity_id} to {temperature}°"
