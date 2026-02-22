from __future__ import annotations
from typing import Any


async def get_events(calendar_entity: str, ha_client: Any = None, **kwargs) -> str:
    if ha_client is None:
        return f"HA client unavailable — cannot read {calendar_entity}"
    state = await ha_client.get_state(calendar_entity)
    return str(state)


async def create_event(
    calendar_entity: str,
    summary: str,
    start_time: str,
    end_time: str,
    ha_client: Any = None,
    **kwargs,
) -> str:
    if ha_client is None:
        return f"HA client unavailable — cannot create event in {calendar_entity}"
    await ha_client.call_service(
        "calendar", "create_event",
        {"entity_id": calendar_entity, "summary": summary, "start_date_time": start_time, "end_date_time": end_time},
    )
    return f"Event '{summary}' created in {calendar_entity}"
