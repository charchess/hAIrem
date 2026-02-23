import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from src.features.home.social_grid.repository import SocialGridRepository
from src.features.home.social_grid.models import (
    RelationshipChangeEvent,
    RelationshipNotification,
    ChangeMagnitude,
    NotificationType,
)


@pytest.fixture
def mock_surreal():
    s = MagicMock()
    s.client = MagicMock()
    s._call = AsyncMock()
    return s


@pytest.fixture
def repo(mock_surreal):
    return SocialGridRepository(surreal_client=mock_surreal)


@pytest.fixture
def event():
    return RelationshipChangeEvent(
        relationship_type="agent_user",
        party_a="lisa",
        party_b="user1",
        old_status="stranger",
        new_status="acquaintance",
        old_score=10.0,
        new_score=35.0,
        change_magnitude=ChangeMagnitude.MAJOR,
        timestamp=datetime(2024, 1, 1),
    )


@pytest.mark.asyncio
async def test_save_relationship_event_calls_create(repo, mock_surreal, event):
    mock_surreal._call.return_value = {"id": "relationship_events:abc"}

    result = await repo.save_relationship_event(event)

    assert result is True
    mock_surreal._call.assert_called_once_with("create", "relationship_events", event.to_dict())


@pytest.mark.asyncio
async def test_save_relationship_event_returns_false_when_no_client(mock_surreal, event):
    mock_surreal.client = None
    repo = SocialGridRepository(surreal_client=mock_surreal)
    result = await repo.save_relationship_event(event)
    assert result is False


@pytest.mark.asyncio
async def test_save_relationship_event_returns_false_on_exception(repo, mock_surreal, event):
    mock_surreal._call.side_effect = Exception("DB down")
    result = await repo.save_relationship_event(event)
    assert result is False


@pytest.mark.asyncio
async def test_get_recent_events_returns_list(repo, mock_surreal):
    event_dict = {
        "relationship_type": "agent_user",
        "party_a": "lisa",
        "party_b": "user1",
        "old_status": None,
        "new_status": "friend",
        "old_score": 0.0,
        "new_score": 50.0,
        "change_magnitude": "major",
        "timestamp": "2024-01-01T00:00:00",
    }
    mock_surreal._call.return_value = [{"result": [event_dict]}]

    events = await repo.get_recent_events()
    assert len(events) == 1
    assert events[0].party_a == "lisa"


@pytest.mark.asyncio
async def test_get_recent_events_filtered_by_type(repo, mock_surreal):
    mock_surreal._call.return_value = [{"result": []}]
    events = await repo.get_recent_events(relationship_type="agent_user")
    assert events == []
    query = mock_surreal._call.call_args[0][1]
    assert "agent_user" in query


@pytest.mark.asyncio
async def test_save_grid_state_calls_delete_then_create(repo, mock_surreal):
    mock_surreal._call.return_value = None

    result = await repo.save_grid_state({"agent_user_relationships_count": 5})

    assert result is True
    calls = mock_surreal._call.call_args_list
    assert "DELETE" in calls[0][0][1]
    assert calls[1][0][0] == "create"


@pytest.mark.asyncio
async def test_load_grid_state_returns_dict(repo, mock_surreal):
    mock_surreal._call.return_value = [{"result": [{"agent_user_relationships_count": 3}]}]

    state = await repo.load_grid_state()

    assert state is not None
    assert state["agent_user_relationships_count"] == 3


@pytest.mark.asyncio
async def test_load_grid_state_returns_none_when_empty(repo, mock_surreal):
    mock_surreal._call.return_value = [{"result": []}]
    state = await repo.load_grid_state()
    assert state is None


@pytest.mark.asyncio
async def test_no_surreal_client_returns_safe_defaults():
    repo = SocialGridRepository(surreal_client=None)
    events = await repo.get_recent_events()
    state = await repo.load_grid_state()
    count = await repo.get_unread_count("user1")
    assert events == []
    assert state is None
    assert count == 0
