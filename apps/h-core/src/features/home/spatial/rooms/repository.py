import logging
from typing import Optional

from src.features.home.spatial.rooms.models import Room, RoomAssignment

logger = logging.getLogger(__name__)


class RoomRepository:
    TABLE_NAME = "room"
    ASSIGNMENT_TABLE = "agent_room"

    def __init__(self, surreal_client):
        self.surreal = surreal_client

    async def create_room(self, room: Room) -> Room:
        data = {
            "room_id": room.room_id,
            "name": room.name,
            "type": room.type,
            "description": room.description
        }
        await self.surreal._call("create", self.TABLE_NAME, data)
        logger.info(f"RoomRepository: Created room {room.room_id}")
        return room

    async def get_room(self, room_id: str) -> Optional[Room]:
        try:
            result = await self.surreal._call(
                "query",
                f"SELECT * FROM {self.TABLE_NAME} WHERE room_id = $room_id LIMIT 1;",
                {"room_id": room_id}
            )
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                if records and len(records) > 0:
                    record = records[0]
                    return Room(
                        room_id=record.get("room_id"),
                        name=record.get("name"),
                        type=record.get("type", "generic"),
                        description=record.get("description")
                    )
        except Exception as e:
            logger.error(f"RoomRepository: Failed to get room {room_id}: {e}")
        return None

    async def list_rooms(self) -> list[Room]:
        try:
            result = await self.surreal._call("query", f"SELECT * FROM {self.TABLE_NAME};")
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                return [
                    Room(
                        room_id=r.get("room_id"),
                        name=r.get("name"),
                        type=r.get("type", "generic"),
                        description=r.get("description")
                    )
                    for r in records
                ]
        except Exception as e:
            logger.error(f"RoomRepository: Failed to list rooms: {e}")
        return []

    async def update_room(self, room_id: str, name: str = None, type: str = None, description: str = None) -> Optional[Room]:
        updates = {}
        if name is not None:
            updates["name"] = name
        if type is not None:
            updates["type"] = type
        if description is not None:
            updates["description"] = description

        if not updates:
            return await self.get_room(room_id)

        try:
            set_clause = ", ".join([f"{k} = ${k}" for k in updates.keys()])
            await self.surreal._call(
                "query",
                f"UPDATE {self.TABLE_NAME} SET {set_clause} WHERE room_id = $room_id;",
                {**updates, "room_id": room_id}
            )
            logger.info(f"RoomRepository: Updated room {room_id}")
            return await self.get_room(room_id)
        except Exception as e:
            logger.error(f"RoomRepository: Failed to update room {room_id}: {e}")
            return None

    async def delete_room(self, room_id: str) -> bool:
        try:
            await self.surreal._call(
                "query",
                f"DELETE FROM {self.TABLE_NAME} WHERE room_id = $room_id;",
                {"room_id": room_id}
            )
            logger.info(f"RoomRepository: Deleted room {room_id}")
            return True
        except Exception as e:
            logger.error(f"RoomRepository: Failed to delete room {room_id}: {e}")
            return False

    async def assign_agent_to_room(self, agent_id: str, room_id: str) -> bool:
        try:
            existing = await self.surreal._call(
                "query",
                f"SELECT * FROM {self.ASSIGNMENT_TABLE} WHERE agent_id = $agent_id;",
                {"agent_id": agent_id}
            )
            
            if existing and isinstance(existing, list) and len(existing) > 0:
                records = existing[0].get("result", []) if isinstance(existing[0], dict) else existing
                if records and len(records) > 0:
                    await self.surreal._call(
                        "query",
                        f"UPDATE {self.ASSIGNMENT_TABLE} SET room_id = $room_id WHERE agent_id = $agent_id;",
                        {"agent_id": agent_id, "room_id": room_id}
                    )
                else:
                    await self.surreal._call("create", self.ASSIGNMENT_TABLE, {
                        "agent_id": agent_id,
                        "room_id": room_id
                    })
            else:
                await self.surreal._call("create", self.ASSIGNMENT_TABLE, {
                    "agent_id": agent_id,
                    "room_id": room_id
                })
            
            logger.info(f"RoomRepository: Assigned agent {agent_id} to room {room_id}")
            return True
        except Exception as e:
            logger.error(f"RoomRepository: Failed to assign agent {agent_id} to room {room_id}: {e}")
            return False

    async def get_agent_room(self, agent_id: str) -> Optional[str]:
        try:
            result = await self.surreal._call(
                "query",
                f"SELECT * FROM {self.ASSIGNMENT_TABLE} WHERE agent_id = $agent_id LIMIT 1;",
                {"agent_id": agent_id}
            )
            if result and isinstance(result, list) and len(result) > 0:
                records = result[0].get("result", []) if isinstance(result[0], dict) else result
                if records and len(records) > 0:
                    return records[0].get("room_id")
        except Exception as e:
            logger.error(f"RoomRepository: Failed to get room for agent {agent_id}: {e}")
        return None

    async def remove_agent_assignment(self, agent_id: str) -> bool:
        try:
            await self.surreal._call(
                "query",
                f"DELETE FROM {self.ASSIGNMENT_TABLE} WHERE agent_id = $agent_id;",
                {"agent_id": agent_id}
            )
            logger.info(f"RoomRepository: Removed assignment for agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"RoomRepository: Failed to remove assignment for agent {agent_id}: {e}")
            return False
