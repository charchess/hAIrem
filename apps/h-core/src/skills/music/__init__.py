from __future__ import annotations
from typing import Any


async def play_music(entity_id: str, media_content_id: str = "", ha_client: Any = None, **kwargs) -> str:
    if ha_client is None:
        return f"HA client unavailable — cannot play music on {entity_id}"
    await ha_client.call_service(
        "media_player", "play_media",
        {"entity_id": entity_id, "media_content_id": media_content_id, "media_content_type": "music"},
    )
    return f"Playing on {entity_id}"


async def pause_music(entity_id: str, ha_client: Any = None, **kwargs) -> str:
    if ha_client is None:
        return f"HA client unavailable — cannot pause {entity_id}"
    await ha_client.call_service("media_player", "media_pause", {"entity_id": entity_id})
    return f"Paused {entity_id}"


async def set_volume(entity_id: str, volume: float, ha_client: Any = None, **kwargs) -> str:
    if ha_client is None:
        return f"HA client unavailable — cannot set volume on {entity_id}"
    await ha_client.call_service(
        "media_player", "volume_set",
        {"entity_id": entity_id, "volume_level": max(0.0, min(1.0, volume))},
    )
    return f"Volume set to {volume:.0%} on {entity_id}"
