import pytest
from unittest.mock import MagicMock, AsyncMock
from src.features.home.spatial.rooms.models import Room, RoomAssignment
from src.features.home.spatial.rooms.repository import RoomRepository
from src.features.home.spatial.rooms.service import RoomService


@pytest.mark.asyncio
async def test_room_creation():
    mock_surreal = MagicMock()
    mock_surreal._call = AsyncMock(return_value=[{"result": []}])
    
    repository = RoomRepository(mock_surreal)
    room = Room(room_id="living_room", name="Salon", type="living_room", description="Main living area")
    
    created = await repository.create_room(room)
    
    assert created.room_id == "living_room"
    assert created.name == "Salon"
    assert created.type == "living_room"


@pytest.mark.asyncio
async def test_room_assignment():
    mock_surreal = MagicMock()
    mock_surreal._call = AsyncMock(return_value=[{"result": []}])
    
    repository = RoomRepository(mock_surreal)
    
    result = await repository.assign_agent_to_room("agent1", "living_room")
    
    assert result is True


@pytest.mark.asyncio
async def test_get_agent_room():
    mock_surreal = MagicMock()
    mock_surreal._call = AsyncMock(return_value=[{"result": [{"room_id": "living_room"}]}])
    
    repository = RoomRepository(mock_surreal)
    
    room_id = await repository.get_agent_room("agent1")
    
    assert room_id == "living_room"


@pytest.mark.asyncio
async def test_room_service_create_room():
    mock_surreal = MagicMock()
    mock_surreal._call = AsyncMock(return_value=[{"result": []}])
    
    service = RoomService(mock_surreal)
    
    result = await service.create_room("bedroom", "Chambre", "bedroom", "Master bedroom")
    
    assert result["success"] is True
    assert result["room"]["room_id"] == "bedroom"
    assert result["room"]["name"] == "Chambre"


@pytest.mark.asyncio
async def test_room_service_assign_agent():
    mock_surreal = MagicMock()
    mock_surreal._call = AsyncMock(return_value=[{"result": [{"room_id": "kitchen"}]}])
    
    mock_agent_registry = MagicMock()
    mock_agent = MagicMock()
    mock_agent.config = MagicMock()
    mock_agent_registry.agents = {"chef": mock_agent}
    
    service = RoomService(mock_surreal, mock_agent_registry)
    service._room_cache = {"kitchen": Room(room_id="kitchen", name="Cuisine", type="kitchen")}
    
    result = await service.assign_agent_to_room("chef", "kitchen")
    
    assert result["success"] is True
    assert mock_agent.config.room_id == "kitchen"


@pytest.mark.asyncio
async def test_room_model():
    room = Room(room_id="office", name="Bureau", type="office", description="Home office")
    
    assert room.room_id == "office"
    assert room.name == "Bureau"
    assert room.type == "office"
    assert room.description == "Home office"


@pytest.mark.asyncio
async def test_room_assignment_model():
    assignment = RoomAssignment(agent_id="assistant", room_id="hallway")
    
    assert assignment.agent_id == "assistant"
    assert assignment.room_id == "hallway"
