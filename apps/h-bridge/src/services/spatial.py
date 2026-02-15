import logging
import sys
import os
from typing import Optional, List
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

SUPPORTED_ROOMS = [
    {"room_id": "living-room", "name": "Living Room", "type": "living"},
    {"room_id": "kitchen", "name": "Kitchen", "type": "kitchen"},
    {"room_id": "bedroom", "name": "Bedroom", "type": "bedroom"},
    {"room_id": "bathroom", "name": "Bathroom", "type": "bathroom"},
    {"room_id": "office", "name": "Office", "type": "office"},
    {"room_id": "garden", "name": "Garden", "type": "garden"},
    {"room_id": "exterior", "name": "Exterior", "type": "exterior"},
]

SUPPORTED_THEMES = [
    {"name": "neutral", "display_name": "Neutral", "mood": {"adjective": "neutral", "description": "Standard everyday mood"}},
    {"name": "christmas", "display_name": "Christmas", "mood": {"adjective": "festive", "description": "Holiday spirit"}},
    {"name": "halloween", "display_name": "Halloween", "mood": {"adjective": "spooky", "description": "Spooky atmosphere"}},
    {"name": "summer", "display_name": "Summer", "mood": {"adjective": "vibrant", "description": "Warm vacation vibes"}},
    {"name": "winter", "display_name": "Winter", "mood": {"adjective": "cozy", "description": "Cold and cozy"}},
]


class SpatialAPIService:
    def __init__(self, surreal_client):
        self.surreal_client = surreal_client
        self._agent_rooms: dict[str, str] = {}
        self._agent_locations: dict[str, dict] = {}
        self._location_history: dict[str, List[dict]] = {}
        self._user_spaces: dict[str, str] = {}
        self._current_theme: str = "neutral"

    async def initialize(self):
        logger.info("SpatialAPIService: Initializing (standalone mode)")
        
        for room in SUPPORTED_ROOMS:
            try:
                await self.surreal_client._call('query',
                    f"INSERT INTO room (id, name, type) VALUES ({room['room_id']}, $name, $type) ON DUPLICATE KEY UPDATE name = $name;",
                    {"name": room["name"], "type": room["type"]}
                )
            except Exception as e:
                logger.debug(f"Room creation: {e}")

    async def get_rooms(self) -> list[dict]:
        return SUPPORTED_ROOMS

    async def get_room_agents(self, room_id: str) -> list[dict]:
        agents = []
        for agent_id, assigned_room in self._agent_rooms.items():
            if assigned_room == room_id:
                agents.append({"agent_id": agent_id})
        return agents

    async def assign_agent_to_room(self, agent_id: str, room_id: str) -> dict:
        valid_rooms = [r["room_id"] for r in SUPPORTED_ROOMS]
        if room_id not in valid_rooms:
            return {"success": False, "error": f"Invalid room: {room_id}"}
        
        self._agent_rooms[agent_id] = room_id
        
        self._agent_locations[agent_id] = {
            "agent_id": agent_id,
            "room_id": room_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "confidence": {"level": "high", "reason": "manual_assignment"}
        }
        
        if agent_id not in self._location_history:
            self._location_history[agent_id] = []
        self._location_history[agent_id].append({
            "agent_id": agent_id,
            "room_id": room_id,
            "timestamp": datetime.now(UTC).isoformat()
        })
        
        return {
            "success": True,
            "agent_id": agent_id,
            "room": {"room_id": room_id, "name": next((r["name"] for r in SUPPORTED_ROOMS if r["room_id"] == room_id), room_id)}
        }

    async def remove_agent_from_room(self, agent_id: str) -> dict:
        if agent_id in self._agent_rooms:
            del self._agent_rooms[agent_id]
        return {"success": True, "agent_id": agent_id}

    async def get_agent_room(self, agent_id: str) -> Optional[dict]:
        room_id = self._agent_rooms.get(agent_id)
        if not room_id:
            return None
        return {
            "room_id": room_id,
            "name": next((r["name"] for r in SUPPORTED_ROOMS if r["room_id"] == room_id), room_id),
            "type": next((r["type"] for r in SUPPORTED_ROOMS if r["room_id"] == room_id), "generic")
        }

    async def get_agent_location(self, agent_id: str) -> Optional[dict]:
        return self._agent_locations.get(agent_id)

    async def update_agent_location(self, agent_id: str, room_id: str, confidence: Optional[dict] = None) -> dict:
        valid_rooms = [r["room_id"] for r in SUPPORTED_ROOMS]
        if room_id not in valid_rooms:
            return {"success": False, "error": f"Invalid room: {room_id}"}
        
        location = {
            "agent_id": agent_id,
            "room_id": room_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "confidence": confidence or {"level": "high", "reason": "manual_update"}
        }
        
        self._agent_locations[agent_id] = location
        
        if agent_id not in self._location_history:
            self._location_history[agent_id] = []
        self._location_history[agent_id].append(location)
        
        self._agent_rooms[agent_id] = room_id
        
        return {
            "success": True,
            "location": location
        }

    async def get_agent_location_history(self, agent_id: str, limit: int = 10) -> list[dict]:
        history = self._location_history.get(agent_id, [])
        return history[-limit:]

    async def handle_mobile_location(self, data: dict) -> dict:
        user_id = data.get("user_id", "unknown")
        location = data.get("location", {})
        room = data.get("location") if isinstance(data.get("location"), str) else None
        
        lat = location.get("lat") if isinstance(location, dict) else None
        lng = location.get("lng") if isinstance(location, dict) else None
        
        room = data.get("location") if isinstance(data.get("location"), str) else None
        
        if room and room not in [r["room_id"] for r in SUPPORTED_ROOMS]:
            room = None
        
        if room:
            return await self.update_agent_location(user_id, room)
        
        return {
            "success": True,
            "message": "Location received",
            "location": {"latitude": lat, "longitude": lng, "room_id": room}
        }

    async def get_exterior_info(self) -> dict:
        return {
            "exterior_id": "exterior",
            "name": "Exterior",
            "type": "exterior",
            "description": "Outside the home structure"
        }

    async def set_user_space(self, user_id: str, space: str) -> dict:
        self._user_spaces[user_id] = space
        
        if space == "exterior":
            self._agent_rooms[user_id] = "exterior"
            return {
                "success": True,
                "user_id": user_id,
                "space": "exterior",
                "context": {"is_exterior": True}
            }
        else:
            return {
                "success": True,
                "user_id": user_id,
                "space": "interior"
            }

    async def get_themes(self) -> list[dict]:
        return SUPPORTED_THEMES

    async def set_theme(self, theme_name: str) -> dict:
        valid_themes = [t["name"] for t in SUPPORTED_THEMES]
        if theme_name not in valid_themes:
            return {"success": False, "error": f"Invalid theme: {theme_name}"}
        
        self._current_theme = theme_name
        return {
            "success": True,
            "theme": theme_name,
            "message": f"Theme set to {theme_name}"
        }

    async def get_agent_theme(self, agent_id: str) -> dict:
        return {
            "agent_id": agent_id,
            "theme": self._current_theme,
            "display_name": next((t["display_name"] for t in SUPPORTED_THEMES if t["name"] == self._current_theme), "Neutral"),
            "mood": next((t["mood"] for t in SUPPORTED_THEMES if t["name"] == self._current_theme), {"adjective": "neutral", "description": "Standard"})
        }
