import logging
from typing import Optional, List
from datetime import datetime, timedelta, UTC

from src.features.home.spatial.location.models import AgentLocation, LocationConfidence
from src.features.home.spatial.location.repository import LocationRepository

logger = logging.getLogger(__name__)


class LocationService:
    def __init__(self, surreal_client, room_service=None):
        self.repository = LocationRepository(surreal_client)
        self.room_service = room_service

    async def initialize(self):
        logger.info("LocationService: Initializing...")

    async def update_agent_location(
        self,
        agent_id: str,
        room_id: str,
        confidence: Optional[LocationConfidence] = None
    ) -> dict:
        if not agent_id or not agent_id.strip():
            return {"success": False, "error": "agent_id is required"}
        if not room_id or not room_id.strip():
            return {"success": False, "error": "room_id is required"}

        if self.room_service:
            room = await self.room_service.get_room(room_id)
            if not room:
                return {"success": False, "error": f"Room {room_id} not found"}

        try:
            location = AgentLocation(
                agent_id=agent_id,
                room_id=room_id,
                timestamp=datetime.now(UTC),
                confidence=confidence
            )
            saved = await self.repository.save_location(location)
            
            logger.info(f"LocationService: Updated location for agent {agent_id} to room {room_id}")
            return {
                "success": True,
                "location": {
                    "agent_id": saved.agent_id,
                    "room_id": saved.room_id,
                    "timestamp": saved.timestamp.isoformat() if saved.timestamp else None,
                    "confidence": {
                        "level": saved.confidence.level if saved.confidence else "high",
                        "reason": saved.confidence.reason if saved.confidence else None
                    } if saved.confidence else None
                }
            }
        except Exception as e:
            logger.error(f"LocationService: Failed to update location for agent {agent_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_current_location(self, agent_id: str) -> Optional[dict]:
        location = await self.repository.get_current_location(agent_id)
        if not location:
            return None

        return {
            "agent_id": location.agent_id,
            "room_id": location.room_id,
            "timestamp": location.timestamp.isoformat() if location.timestamp else None,
            "confidence": {
                "level": location.confidence.level if location.confidence else "high",
                "reason": location.confidence.reason if location.confidence else None
            } if location.confidence else None
        }

    async def get_location_history(self, agent_id: str, limit: int = 10) -> List[dict]:
        locations = await self.repository.get_location_history(agent_id, limit)
        return [
            {
                "agent_id": loc.agent_id,
                "room_id": loc.room_id,
                "timestamp": loc.timestamp.isoformat() if loc.timestamp else None,
                "confidence": {
                    "level": loc.confidence.level if loc.confidence else "high",
                    "reason": loc.confidence.reason if loc.confidence else None
                } if loc.confidence else None
            }
            for loc in locations
        ]

    async def get_recent_locations(self, agent_id: str, minutes: int = 60) -> List[dict]:
        since = datetime.now(UTC) - timedelta(minutes=minutes)
        locations = await self.repository.get_recent_locations(agent_id, since)
        return [
            {
                "agent_id": loc.agent_id,
                "room_id": loc.room_id,
                "timestamp": loc.timestamp.isoformat() if loc.timestamp else None,
                "confidence": {
                    "level": loc.confidence.level if loc.confidence else "high",
                    "reason": loc.confidence.reason if loc.confidence else None
                } if loc.confidence else None
            }
            for loc in locations
        ]

    async def track_ambiguous_location(
        self,
        agent_id: str,
        room_id: str,
        confidence_level: str = "medium",
        confidence_reason: Optional[str] = None
    ) -> dict:
        confidence = LocationConfidence(
            level=confidence_level,
            reason=confidence_reason
        )
        return await self.update_agent_location(agent_id, room_id, confidence)
