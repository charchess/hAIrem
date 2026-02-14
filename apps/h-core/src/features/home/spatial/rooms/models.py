from pydantic import BaseModel, Field
from typing import Optional


class Room(BaseModel):
    room_id: str = Field(..., min_length=1, description="Unique room identifier")
    name: str = Field(..., min_length=1, description="Room name")
    type: str = Field(default="generic", description="Room type (e.g., living_room, bedroom, kitchen)")
    description: Optional[str] = Field(default=None, description="Room description")


class RoomAssignment(BaseModel):
    agent_id: str = Field(..., min_length=1, description="Agent identifier")
    room_id: str = Field(..., min_length=1, description="Room identifier")
