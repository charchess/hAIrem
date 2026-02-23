import pytest
from unittest.mock import AsyncMock, MagicMock, call


@pytest.fixture
def mock_surreal():
    s = MagicMock()
    s._call = AsyncMock()
    s.update_agent_state = AsyncMock()
    s.move_agent_to_location = AsyncMock(return_value=True)
    s.get_agents_in_location = AsyncMock(return_value=["lisa", "renarde"])
    s.get_agent_location = AsyncMock(return_value="salon")
    return s


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.publish_event = AsyncMock()
    return r


@pytest.mark.asyncio
async def test_move_agent_to_location_calls_three_queries():
    from src.infrastructure.surrealdb import SurrealDbClient

    surreal = SurrealDbClient(url="ws://localhost:8000", user="root", password="root")
    surreal._call = AsyncMock()
    surreal.update_agent_state = AsyncMock()

    result = await surreal.move_agent_to_location("Lisa", "salon")

    assert surreal._call.call_count == 3
    assert surreal.update_agent_state.call_count == 1
    calls_str = " ".join(str(c) for c in surreal._call.call_args_list)
    assert "INSERT INTO location" in calls_str
    assert "DELETE PRESENT_IN" in calls_str
    assert "RELATE" in calls_str


@pytest.mark.asyncio
async def test_get_agents_in_location_returns_names():
    from src.infrastructure.surrealdb import SurrealDbClient

    surreal = SurrealDbClient(url="ws://localhost:8000", user="root", password="root")
    surreal._call = AsyncMock(return_value=[{"result": [{"agent_name": "lisa"}, {"agent_name": "renarde"}]}])

    result = await surreal.get_agents_in_location("salon")

    assert result == ["lisa", "renarde"]


@pytest.mark.asyncio
async def test_get_agents_in_location_returns_empty_on_no_results():
    from src.infrastructure.surrealdb import SurrealDbClient

    surreal = SurrealDbClient(url="ws://localhost:8000", user="root", password="root")
    surreal._call = AsyncMock(return_value=[{"result": []}])

    result = await surreal.get_agents_in_location("unknown_room")

    assert result == []


@pytest.mark.asyncio
async def test_get_agent_location_returns_location_name():
    from src.infrastructure.surrealdb import SurrealDbClient

    surreal = SurrealDbClient(url="ws://localhost:8000", user="root", password="root")
    surreal._call = AsyncMock(return_value=[{"result": [{"loc_name": "jardin"}]}])

    result = await surreal.get_agent_location("renarde")

    assert result == "jardin"


@pytest.mark.asyncio
async def test_get_agent_location_returns_none_when_not_placed():
    from src.infrastructure.surrealdb import SurrealDbClient

    surreal = SurrealDbClient(url="ws://localhost:8000", user="root", password="root")
    surreal._call = AsyncMock(return_value=[{"result": []}])

    result = await surreal.get_agent_location("electra")

    assert result is None


@pytest.mark.asyncio
async def test_spatial_registry_move_agent_calls_surreal_and_broadcasts(mock_surreal, mock_redis):
    from src.features.home.spatial.registry import SpatialRegistry

    registry = SpatialRegistry(surreal=mock_surreal, redis=mock_redis)

    result = await registry.move_agent("lisa", "jardin")

    assert result is True
    mock_surreal.move_agent_to_location.assert_awaited_once_with("lisa", "jardin")
    mock_redis.publish_event.assert_awaited_once()
    event_call = mock_redis.publish_event.call_args
    payload = event_call[0][1]
    assert payload["type"] == "location.change"
    assert payload["payload"]["content"]["agent_id"] == "lisa"
    assert payload["payload"]["content"]["location"] == "jardin"


@pytest.mark.asyncio
async def test_spatial_registry_move_agent_fallback_no_method(mock_redis):
    from src.features.home.spatial.registry import SpatialRegistry

    surreal_no_method = MagicMock()
    surreal_no_method.update_agent_state = AsyncMock()
    del surreal_no_method.move_agent_to_location

    registry = SpatialRegistry(surreal=surreal_no_method, redis=mock_redis)

    result = await registry.move_agent("renarde", "cuisine")

    assert result is True
    surreal_no_method.update_agent_state.assert_awaited_once()
    mock_redis.publish_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_agent_move_to_room_uses_spatial_service(mock_surreal):
    from src.domain.agent import BaseAgent
    from src.domain.agent import AgentConfig

    spatial_mock = MagicMock()
    spatial_mock.move_agent = AsyncMock()

    mock_llm = MagicMock()
    mock_llm.model = "test"
    mock_llm.cache = None
    mock_redis = MagicMock()

    config = AgentConfig(name="lisa", role="assistant")
    agent = BaseAgent(
        config=config,
        redis_client=mock_redis,
        llm_client=mock_llm,
        surreal_client=mock_surreal,
        spatial_registry=spatial_mock,
    )

    result = await agent.move_to_room("jardin")

    assert "jardin" in result
    spatial_mock.move_agent.assert_awaited_once_with("lisa", "jardin")


@pytest.mark.asyncio
async def test_agent_move_to_room_fallback_to_direct_db(mock_surreal):
    from src.domain.agent import BaseAgent
    from src.domain.agent import AgentConfig

    mock_llm = MagicMock()
    mock_llm.model = "test"
    mock_llm.cache = None
    mock_redis = MagicMock()

    config = AgentConfig(name="electra", role="assistant")
    agent = BaseAgent(
        config=config,
        redis_client=mock_redis,
        llm_client=mock_llm,
        surreal_client=mock_surreal,
    )

    result = await agent.move_to_room("bureau")

    assert "bureau" in result
    mock_surreal.update_agent_state.assert_awaited_once_with(
        "electra", "IS_IN", {"name": "bureau", "description": "The bureau"}
    )
