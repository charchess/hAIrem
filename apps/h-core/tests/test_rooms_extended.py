import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from features.home.spatial.rooms.service import RoomService
from features.home.spatial.rooms.repository import RoomRepository
from features.home.spatial.rooms.models import Room, RoomAssignment


def make_surreal(room_result=None):
    surreal = MagicMock()
    surreal.client = MagicMock()
    if room_result is None:
        surreal._call = AsyncMock(return_value=[{"result": []}])
    else:
        surreal._call = AsyncMock(return_value=room_result)
    return surreal


def room_data(room_id="r1", name="Living Room", type="living", description="main room"):
    return {"room_id": room_id, "name": name, "type": type, "description": description}


class TestRoomRepository:
    @pytest.mark.asyncio
    async def test_create_room(self):
        surreal = make_surreal()
        repo = RoomRepository(surreal)
        room = Room(room_id="r1", name="Living Room", type="living")
        result = await repo.create_room(room)
        assert result.room_id == "r1"
        surreal._call.assert_called()

    @pytest.mark.asyncio
    async def test_get_room_found(self):
        surreal = make_surreal([{"result": [room_data()]}])
        repo = RoomRepository(surreal)
        result = await repo.get_room("r1")
        assert result is not None
        assert result.room_id == "r1"

    @pytest.mark.asyncio
    async def test_get_room_not_found(self):
        surreal = make_surreal([{"result": []}])
        repo = RoomRepository(surreal)
        result = await repo.get_room("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_room_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = RoomRepository(surreal)
        result = await repo.get_room("r1")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_rooms_empty(self):
        surreal = make_surreal([{"result": []}])
        repo = RoomRepository(surreal)
        result = await repo.list_rooms()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_rooms_with_data(self):
        surreal = make_surreal([{"result": [room_data("r1"), room_data("r2", name="Kitchen")]}])
        repo = RoomRepository(surreal)
        result = await repo.list_rooms()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_rooms_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = RoomRepository(surreal)
        result = await repo.list_rooms()
        assert result == []

    @pytest.mark.asyncio
    async def test_update_room_no_fields_calls_get(self):
        surreal = make_surreal([{"result": [room_data()]}])
        repo = RoomRepository(surreal)
        result = await repo.update_room("r1")
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_room_with_fields(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=[None, [{"result": [room_data(name="Updated")]}]])
        repo = RoomRepository(surreal)
        result = await repo.update_room("r1", name="Updated")
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_room_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = RoomRepository(surreal)
        result = await repo.update_room("r1", name="Bad")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_room_success(self):
        surreal = make_surreal()
        repo = RoomRepository(surreal)
        result = await repo.delete_room("r1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_room_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = RoomRepository(surreal)
        result = await repo.delete_room("r1")
        assert result is False

    @pytest.mark.asyncio
    async def test_assign_agent_no_existing_assignment(self):
        surreal = make_surreal([{"result": []}])
        repo = RoomRepository(surreal)
        result = await repo.assign_agent_to_room("agent1", "r1")
        assert result is True

    @pytest.mark.asyncio
    async def test_assign_agent_updates_existing(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(
            side_effect=[
                [{"result": [{"agent_id": "agent1", "room_id": "r0"}]}],
                None,
            ]
        )
        repo = RoomRepository(surreal)
        result = await repo.assign_agent_to_room("agent1", "r1")
        assert result is True

    @pytest.mark.asyncio
    async def test_assign_agent_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = RoomRepository(surreal)
        result = await repo.assign_agent_to_room("agent1", "r1")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_agent_room_found(self):
        surreal = make_surreal([{"result": [{"agent_id": "agent1", "room_id": "r1"}]}])
        repo = RoomRepository(surreal)
        result = await repo.get_agent_room("agent1")
        assert result == "r1"

    @pytest.mark.asyncio
    async def test_get_agent_room_not_found(self):
        surreal = make_surreal([{"result": []}])
        repo = RoomRepository(surreal)
        result = await repo.get_agent_room("unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_agent_room_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = RoomRepository(surreal)
        result = await repo.get_agent_room("agent1")
        assert result is None

    @pytest.mark.asyncio
    async def test_remove_agent_assignment_success(self):
        surreal = make_surreal()
        repo = RoomRepository(surreal)
        result = await repo.remove_agent_assignment("agent1")
        assert result is True

    @pytest.mark.asyncio
    async def test_remove_agent_assignment_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = RoomRepository(surreal)
        result = await repo.remove_agent_assignment("agent1")
        assert result is False


class TestRoomService:
    @pytest.mark.asyncio
    async def test_initialize_loads_rooms(self):
        surreal = make_surreal([{"result": [room_data()]}])
        service = RoomService(surreal)
        await service.initialize()
        assert len(service._room_cache) == 1

    @pytest.mark.asyncio
    async def test_create_room_success(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        result = await service.create_room("r1", "Living Room", type="living")
        assert result["success"] is True
        assert result["room"]["room_id"] == "r1"

    @pytest.mark.asyncio
    async def test_create_room_missing_room_id(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        result = await service.create_room("", "Living Room")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_create_room_missing_name(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        result = await service.create_room("r1", "")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_create_room_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        service = RoomService(surreal)
        result = await service.create_room("r1", "Living Room")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_room_from_cache(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        cached_room = Room(room_id="r1", name="Living", type="living")
        service._room_cache["r1"] = cached_room
        result = await service.get_room("r1")
        assert result.room_id == "r1"

    @pytest.mark.asyncio
    async def test_get_room_from_db(self):
        surreal = make_surreal([{"result": [room_data()]}])
        service = RoomService(surreal)
        result = await service.get_room("r1")
        assert result is not None
        assert "r1" in service._room_cache

    @pytest.mark.asyncio
    async def test_get_room_not_found(self):
        surreal = make_surreal([{"result": []}])
        service = RoomService(surreal)
        result = await service.get_room("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_rooms(self):
        surreal = make_surreal([{"result": [room_data("r1"), room_data("r2", name="Kitchen")]}])
        service = RoomService(surreal)
        result = await service.list_rooms()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_room_success(self):
        surreal = make_surreal()
        updated = room_data(name="Updated")
        surreal._call = AsyncMock(side_effect=[None, [{"result": [updated]}]])
        service = RoomService(surreal)
        result = await service.update_room("r1", name="Updated")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_room_not_found(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=[None, [{"result": []}]])
        service = RoomService(surreal)
        result = await service.update_room("r1", name="Updated")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_delete_room_success(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        service._room_cache["r1"] = Room(room_id="r1", name="Living", type="living")
        result = await service.delete_room("r1")
        assert result["success"] is True
        assert "r1" not in service._room_cache

    @pytest.mark.asyncio
    async def test_delete_room_not_in_cache(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        result = await service.delete_room("r1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_assign_agent_to_room_success(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        service._room_cache["r1"] = Room(room_id="r1", name="Living", type="living")
        surreal._call = AsyncMock(return_value=[{"result": []}])
        result = await service.assign_agent_to_room("agent1", "r1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_assign_agent_missing_agent_id(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        result = await service.assign_agent_to_room("", "r1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_assign_agent_missing_room_id(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        result = await service.assign_agent_to_room("agent1", "")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_assign_agent_room_not_found(self):
        surreal = make_surreal([{"result": []}])
        service = RoomService(surreal)
        result = await service.assign_agent_to_room("agent1", "missing")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_assign_agent_repo_returns_false(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        service._room_cache["r1"] = Room(room_id="r1", name="Living", type="living")
        service.repository.assign_agent_to_room = AsyncMock(return_value=False)
        result = await service.assign_agent_to_room("agent1", "r1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_assign_agent_exception(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        service._room_cache["r1"] = Room(room_id="r1", name="Living", type="living")
        service.repository.assign_agent_to_room = AsyncMock(side_effect=Exception("fail"))
        result = await service.assign_agent_to_room("agent1", "r1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_agent_room_found(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        service._room_cache["r1"] = Room(room_id="r1", name="Living", type="living")
        service.repository.get_agent_room = AsyncMock(return_value="r1")
        result = await service.get_agent_room("agent1")
        assert result is not None
        assert result["room_id"] == "r1"

    @pytest.mark.asyncio
    async def test_get_agent_room_no_assignment(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        service.repository.get_agent_room = AsyncMock(return_value=None)
        result = await service.get_agent_room("agent1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_agent_room_room_missing(self):
        surreal = make_surreal([{"result": []}])
        service = RoomService(surreal)
        service.repository.get_agent_room = AsyncMock(return_value="r_missing")
        result = await service.get_agent_room("agent1")
        assert result is None

    @pytest.mark.asyncio
    async def test_remove_agent_assignment(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        result = await service.remove_agent_assignment("agent1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_agent_location_with_registry(self):
        surreal = make_surreal()
        mock_agent = MagicMock()
        mock_agent.config = MagicMock()
        mock_agent.config.room_id = None
        mock_registry = MagicMock()
        mock_registry.agents = {"agent1": mock_agent}
        service = RoomService(surreal, agent_registry=mock_registry)
        room = Room(room_id="r1", name="Living", type="living")
        await service._update_agent_location("agent1", room)
        assert mock_agent.config.room_id == "r1"

    @pytest.mark.asyncio
    async def test_update_agent_location_no_registry(self):
        surreal = make_surreal()
        service = RoomService(surreal)
        room = Room(room_id="r1", name="Living", type="living")
        await service._update_agent_location("agent1", room)

    @pytest.mark.asyncio
    async def test_update_agent_location_agent_not_in_registry(self):
        surreal = make_surreal()
        mock_registry = MagicMock()
        mock_registry.agents = {}
        service = RoomService(surreal, agent_registry=mock_registry)
        room = Room(room_id="r1", name="Living", type="living")
        await service._update_agent_location("unknown_agent", room)
