import logging
from typing import Optional

from src.features.home.spatial.rooms.models import Room, RoomAssignment
from src.features.home.spatial.rooms.repository import RoomRepository

logger = logging.getLogger(__name__)


class RoomService:
    def __init__(self, surreal_client, agent_registry=None):
        self.repository = RoomRepository(surreal_client)
        self.agent_registry = agent_registry
        self._room_cache: dict[str, Room] = {}

    async def initialize(self):
        logger.info("RoomService: Initializing...")
        await self._load_all_rooms()

    async def _load_all_rooms(self):
        rooms = await self.repository.list_rooms()
        for room in rooms:
            self._room_cache[room.room_id] = room
        logger.info(f"RoomService: Loaded {len(self._room_cache)} rooms")

    async def create_room(self, room_id: str, name: str, type: str = "generic", description: str = None) -> dict:
        if not room_id or not room_id.strip():
            return {"success": False, "error": "room_id is required"}
        if not name or not name.strip():
            return {"success": False, "error": "name is required"}

        try:
            room = Room(room_id=room_id, name=name, type=type, description=description)
            created = await self.repository.create_room(room)
            self._room_cache[created.room_id] = created
            logger.info(f"RoomService: Created room {room_id}")
            return {
                "success": True,
                "room": {
                    "room_id": created.room_id,
                    "name": created.name,
                    "type": created.type,
                    "description": created.description
                }
            }
        except Exception as e:
            logger.error(f"RoomService: Failed to create room {room_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_room(self, room_id: str) -> Optional[Room]:
        if room_id in self._room_cache:
            return self._room_cache[room_id]
        room = await self.repository.get_room(room_id)
        if room:
            self._room_cache[room_id] = room
        return room

    async def list_rooms(self) -> list[dict]:
        rooms = await self.repository.list_rooms()
        return [
            {
                "room_id": r.room_id,
                "name": r.name,
                "type": r.type,
                "description": r.description
            }
            for r in rooms
        ]

    async def update_room(self, room_id: str, name: str = None, type: str = None, description: str = None) -> dict:
        room = await self.repository.update_room(room_id, name, type, description)
        if room:
            self._room_cache[room_id] = room
            return {
                "success": True,
                "room": {
                    "room_id": room.room_id,
                    "name": room.name,
                    "type": room.type,
                    "description": room.description
                }
            }
        return {"success": False, "error": "Room not found"}

    async def delete_room(self, room_id: str) -> dict:
        result = await self.repository.delete_room(room_id)
        if result and room_id in self._room_cache:
            del self._room_cache[room_id]
        return {"success": result, "room_id": room_id}

    async def assign_agent_to_room(self, agent_id: str, room_id: str) -> dict:
        if not agent_id or not agent_id.strip():
            return {"success": False, "error": "agent_id is required"}
        if not room_id or not room_id.strip():
            return {"success": False, "error": "room_id is required"}

        room = await self.get_room(room_id)
        if not room:
            return {"success": False, "error": f"Room {room_id} not found"}

        try:
            result = await self.repository.assign_agent_to_room(agent_id, room_id)
            if result:
                await self._update_agent_location(agent_id, room)
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "room": {
                        "room_id": room.room_id,
                        "name": room.name,
                        "type": room.type
                    }
                }
            return {"success": False, "error": "Failed to assign agent to room"}
        except Exception as e:
            logger.error(f"RoomService: Failed to assign agent {agent_id} to room {room_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_agent_room(self, agent_id: str) -> Optional[dict]:
        room_id = await self.repository.get_agent_room(agent_id)
        if not room_id:
            return None

        room = await self.get_room(room_id)
        if not room:
            return None

        return {
            "room_id": room.room_id,
            "name": room.name,
            "type": room.type,
            "description": room.description
        }

    async def remove_agent_assignment(self, agent_id: str) -> dict:
        result = await self.repository.remove_agent_assignment(agent_id)
        return {"success": result, "agent_id": agent_id}

    async def _update_agent_location(self, agent_id: str, room: Room):
        if self.agent_registry and agent_id in self.agent_registry.agents:
            agent = self.agent_registry.agents[agent_id]
            if hasattr(agent, "config") and agent.config:
                agent.config.room_id = room.room_id
                logger.info(f"RoomService: Updated agent {agent_id} location to room {room.room_id}")
