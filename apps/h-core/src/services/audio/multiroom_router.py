import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

ROOM_SPEAKER_MAP: Dict[str, str] = {
    "salon": "media_player.salon",
    "cuisine": "media_player.cuisine",
    "chambre": "media_player.chambre",
    "bureau": "media_player.bureau",
}


class MultiRoomAudioRouter:
    def __init__(self, ha_client=None, room_speaker_map: Optional[Dict[str, str]] = None):
        self.ha_client = ha_client
        self.room_speaker_map = room_speaker_map or ROOM_SPEAKER_MAP

    def resolve_speaker(self, room_id: Optional[str]) -> Optional[str]:
        if not room_id:
            return None
        return self.room_speaker_map.get(room_id.lower())

    def get_speakers_for_room(self, room_id: str) -> List[str]:
        speaker = self.resolve_speaker(room_id)
        return [speaker] if speaker else []

    async def route(self, audio_url: str, room_id: Optional[str], agent_id: str = "") -> bool:
        speaker = self.resolve_speaker(room_id)
        if not speaker:
            logger.info(f"MULTIROOM: No speaker mapping for room '{room_id}', broadcasting globally.")
            return False
        if not self.ha_client:
            logger.warning("MULTIROOM: No HA client configured.")
            return False
        try:
            await self.ha_client.call_service(
                "media_player",
                "play_media",
                {"entity_id": speaker, "media_content_id": audio_url, "media_content_type": "music"},
            )
            logger.info(f"MULTIROOM: Routed {agent_id} audio → {speaker}")
            return True
        except Exception as exc:
            logger.error(f"MULTIROOM: Routing failed for {speaker}: {exc}")
            return False
