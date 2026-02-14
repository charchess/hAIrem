import logging
from typing import Optional, List
from datetime import datetime

from src.features.home.spatial.location.models import AgentLocation, LocationConfidence

logger = logging.getLogger(__name__)


class LocationRepository:
    TABLE_NAME = "agent_location"

    def __init__(self, surreal_client):
        self.surreal = surreal_client

    async def save_location(self, location: AgentLocation) -> AgentLocation:
        data = {
            "agent_id": location.agent_id,
            "room_id": location.room_id,
            "timestamp": location.timestamp.isoformat() if isinstance(location.timestamp, datetime) else location.timestamp,
            "confidence": {
                "level": location.confidence.level if location.confidence else "high",
                "reason": location.confidence.reason if location.confidence else None
            } if location.confidence else None
        }
        await self.surreal._call("create", self.TABLE_NAME, data)
        logger.info(f"LocationRepository: Saved location for agent {location.agent_id} at {location.room_id}")
        return location

    async def get_current_location(self, agent_id: str) -> Optional[AgentLocation]:
        try:
            result = await self.surreal._call(
                "query",
                f"SELECT * FROM {self.TABLE_NAME} WHERE agent_id = $agent_id ORDER BY timestamp DESC LIMIT 1;",
                {"agent_id": agent_id}
            )
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                if records and len(records) > 0:
                    record = records[0]
                    confidence = None
                    if record.get("confidence"):
                        confidence = LocationConfidence(
                            level=record["confidence"].get("level", "high"),
                            reason=record["confidence"].get("reason")
                        )
                    return AgentLocation(
                        agent_id=record.get("agent_id"),
                        room_id=record.get("room_id"),
                        timestamp=record.get("timestamp"),
                        confidence=confidence
                    )
        except Exception as e:
            logger.error(f"LocationRepository: Failed to get current location for agent {agent_id}: {e}")
        return None

    async def get_location_history(self, agent_id: str, limit: int = 10) -> List[AgentLocation]:
        try:
            result = await self.surreal._call(
                "query",
                f"SELECT * FROM {self.TABLE_NAME} WHERE agent_id = $agent_id ORDER BY timestamp DESC LIMIT $limit;",
                {"agent_id": agent_id, "limit": limit}
            )
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                locations = []
                for record in records:
                    confidence = None
                    if record.get("confidence"):
                        confidence = LocationConfidence(
                            level=record["confidence"].get("level", "high"),
                            reason=record["confidence"].get("reason")
                        )
                    locations.append(AgentLocation(
                        agent_id=record.get("agent_id"),
                        room_id=record.get("room_id"),
                        timestamp=record.get("timestamp"),
                        confidence=confidence
                    ))
                return locations
        except Exception as e:
            logger.error(f"LocationRepository: Failed to get location history for agent {agent_id}: {e}")
        return []

    async def get_recent_locations(self, agent_id: str, since: datetime) -> List[AgentLocation]:
        try:
            result = await self.surreal._call(
                "query",
                f"SELECT * FROM {self.TABLE_NAME} WHERE agent_id = $agent_id AND timestamp >= $since ORDER BY timestamp DESC;",
                {"agent_id": agent_id, "since": since.isoformat()}
            )
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                locations = []
                for record in records:
                    confidence = None
                    if record.get("confidence"):
                        confidence = LocationConfidence(
                            level=record["confidence"].get("level", "high"),
                            reason=record["confidence"].get("reason")
                        )
                    locations.append(AgentLocation(
                        agent_id=record.get("agent_id"),
                        room_id=record.get("room_id"),
                        timestamp=record.get("timestamp"),
                        confidence=confidence
                    ))
                return locations
        except Exception as e:
            logger.error(f"LocationRepository: Failed to get recent locations for agent {agent_id}: {e}")
        return []
