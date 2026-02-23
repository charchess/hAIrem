import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from features.home.social_grid import (
    SocialGridService,
    SocialGridRepository,
    RelationshipChangeEvent,
    RelationshipNotification,
    SocialGridState,
    ChangeMagnitude,
    NotificationType,
)
from features.home.user_relationships import RelationshipStatus


def make_surreal():
    surreal = MagicMock()
    surreal.client = MagicMock()
    surreal._call = AsyncMock(return_value=[{"result": []}])
    return surreal


def make_event(**kwargs):
    defaults = dict(
        relationship_type="agent_user",
        party_a="lisa",
        party_b="user123",
        old_status="stranger",
        new_status="friend",
        old_score=10.0,
        new_score=60.0,
        change_magnitude=ChangeMagnitude.MAJOR,
    )
    defaults.update(kwargs)
    return RelationshipChangeEvent(**defaults)


def make_notification(event=None):
    if event is None:
        event = make_event()
    return RelationshipNotification(
        notification_type=NotificationType.STATUS_UPGRADE,
        recipient_id="lisa",
        recipient_type="agent",
        event=event,
        message="Your relationship has improved!",
    )


class TestSocialGridRepositoryWithSurreal:
    @pytest.mark.asyncio
    async def test_setup_schema_success(self):
        surreal = make_surreal()
        repo = SocialGridRepository(surreal)
        await repo.setup_schema()
        surreal._call.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_schema_exception_swallowed(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("DB error"))
        repo = SocialGridRepository(surreal)
        await repo.setup_schema()

    @pytest.mark.asyncio
    async def test_save_relationship_event_success(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value={"id": "re:1"})
        repo = SocialGridRepository(surreal)
        event = make_event()
        result = await repo.save_relationship_event(event)
        assert result is True

    @pytest.mark.asyncio
    async def test_save_relationship_event_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = SocialGridRepository(surreal)
        result = await repo.save_relationship_event(make_event())
        assert result is False

    @pytest.mark.asyncio
    async def test_get_recent_events_no_filter(self):
        surreal = make_surreal()
        event_data = {
            "relationship_type": "agent_user",
            "party_a": "lisa",
            "party_b": "user123",
            "old_status": "stranger",
            "new_status": "friend",
            "old_score": 10.0,
            "new_score": 60.0,
            "change_magnitude": "major",
            "timestamp": "2024-01-15T10:30:00",
        }
        surreal._call = AsyncMock(return_value=[{"result": [event_data]}])
        repo = SocialGridRepository(surreal)
        events = await repo.get_recent_events()
        assert len(events) == 1
        assert events[0].party_a == "lisa"

    @pytest.mark.asyncio
    async def test_get_recent_events_with_filter(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = SocialGridRepository(surreal)
        events = await repo.get_recent_events(relationship_type="agent_user")
        assert events == []

    @pytest.mark.asyncio
    async def test_get_recent_events_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = SocialGridRepository(surreal)
        events = await repo.get_recent_events()
        assert events == []

    @pytest.mark.asyncio
    async def test_save_notification_success(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value={"id": "rn:1"})
        repo = SocialGridRepository(surreal)
        result = await repo.save_notification(make_notification())
        assert result is True

    @pytest.mark.asyncio
    async def test_save_notification_no_surreal(self):
        repo = SocialGridRepository(None)
        result = await repo.save_notification(make_notification())
        assert result is False

    @pytest.mark.asyncio
    async def test_save_notification_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = SocialGridRepository(surreal)
        result = await repo.save_notification(make_notification())
        assert result is False

    @pytest.mark.asyncio
    async def test_get_notifications_for_recipient_all(self):
        surreal = make_surreal()
        notif_data = {
            "notification_type": "status_upgrade",
            "recipient_id": "lisa",
            "recipient_type": "agent",
            "event": make_event().to_dict(),
            "message": "improved",
            "read": False,
        }
        surreal._call = AsyncMock(return_value=[{"result": [notif_data]}])
        repo = SocialGridRepository(surreal)
        notifications = await repo.get_notifications_for_recipient("lisa")
        assert len(notifications) == 1

    @pytest.mark.asyncio
    async def test_get_notifications_for_recipient_unread_only(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = SocialGridRepository(surreal)
        result = await repo.get_notifications_for_recipient("lisa", unread_only=True)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_notifications_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = SocialGridRepository(surreal)
        result = await repo.get_notifications_for_recipient("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_mark_notification_read_success(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=None)
        repo = SocialGridRepository(surreal)
        result = await repo.mark_notification_read("notif-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_mark_notification_read_no_surreal(self):
        repo = SocialGridRepository(None)
        result = await repo.mark_notification_read("notif-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_mark_notification_read_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = SocialGridRepository(surreal)
        result = await repo.mark_notification_read("notif-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_unread_count_success(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=[{"result": [{"count": 5}]}])
        repo = SocialGridRepository(surreal)
        count = await repo.get_unread_count("lisa")
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_unread_count_empty(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = SocialGridRepository(surreal)
        count = await repo.get_unread_count("lisa")
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_unread_count_no_surreal(self):
        repo = SocialGridRepository(None)
        count = await repo.get_unread_count("lisa")
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_unread_count_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = SocialGridRepository(surreal)
        count = await repo.get_unread_count("lisa")
        assert count == 0

    @pytest.mark.asyncio
    async def test_save_grid_state_success(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=None)
        repo = SocialGridRepository(surreal)
        result = await repo.save_grid_state({"agent_user_relationships_count": 5})
        assert result is True

    @pytest.mark.asyncio
    async def test_save_grid_state_no_surreal(self):
        repo = SocialGridRepository(None)
        result = await repo.save_grid_state({})
        assert result is False

    @pytest.mark.asyncio
    async def test_save_grid_state_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = SocialGridRepository(surreal)
        result = await repo.save_grid_state({})
        assert result is False

    @pytest.mark.asyncio
    async def test_load_grid_state_found(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=[{"result": [{"agent_user_relationships_count": 3}]}])
        repo = SocialGridRepository(surreal)
        state = await repo.load_grid_state()
        assert state is not None
        assert state["agent_user_relationships_count"] == 3

    @pytest.mark.asyncio
    async def test_load_grid_state_empty(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = SocialGridRepository(surreal)
        state = await repo.load_grid_state()
        assert state is None

    @pytest.mark.asyncio
    async def test_load_grid_state_no_surreal(self):
        repo = SocialGridRepository(None)
        state = await repo.load_grid_state()
        assert state is None

    @pytest.mark.asyncio
    async def test_load_grid_state_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = SocialGridRepository(surreal)
        state = await repo.load_grid_state()
        assert state is None


class TestSocialGridServiceNotifyChange:
    @pytest.mark.asyncio
    async def test_notify_change_same_status_small_delta_returns_none(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        result = await service._notify_change(
            relationship_type="agent_user",
            party_a="lisa",
            party_b="user123",
            old_status=RelationshipStatus.FRIEND,
            new_status=RelationshipStatus.FRIEND,
            old_score=50.0,
            new_score=55.0,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_notify_change_minor_magnitude_returns_none(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        result = await service._notify_change(
            relationship_type="agent_user",
            party_a="lisa",
            party_b="user123",
            old_status=RelationshipStatus.FRIEND,
            new_status=RelationshipStatus.FRIEND,
            old_score=50.0,
            new_score=60.0,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_notify_change_major_creates_event(self):
        surreal = make_surreal()
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, surreal)
        result = await service._notify_change(
            relationship_type="agent_user",
            party_a="lisa",
            party_b="user123",
            old_status=RelationshipStatus.STRANGER,
            new_status=RelationshipStatus.FRIEND,
            old_score=10.0,
            new_score=60.0,
        )
        assert result is not None
        assert isinstance(result, RelationshipChangeEvent)

    @pytest.mark.asyncio
    async def test_notify_change_none_old_status(self):
        surreal = make_surreal()
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, surreal)
        result = await service._notify_change(
            relationship_type="agent_agent",
            party_a="lisa",
            party_b="max",
            old_status=None,
            new_status=RelationshipStatus.FRIEND,
            old_score=0.0,
            new_score=70.0,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_notify_change_agent_agent_type(self):
        surreal = make_surreal()
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, surreal)
        result = await service._notify_change(
            relationship_type="agent_agent",
            party_a="lisa",
            party_b="max",
            old_status=RelationshipStatus.STRANGER,
            new_status=RelationshipStatus.ALLY,
            old_score=5.0,
            new_score=80.0,
        )
        assert result is not None


class TestSocialGridServiceCreateAndSendNotifications:
    @pytest.mark.asyncio
    async def test_notifications_agent_user_creates_2_notifications(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value={"id": "rn:1"})
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, surreal)

        received = []

        async def callback(notif):
            received.append(notif)

        service.register_notification_callback(callback)
        event = make_event()

        await service._create_and_send_notifications(
            relationship_type="agent_user",
            party_a="lisa",
            party_b="user123",
            old_status=RelationshipStatus.STRANGER,
            new_status=RelationshipStatus.FRIEND,
            old_score=10.0,
            new_score=60.0,
            change_magnitude=ChangeMagnitude.MAJOR,
            event=event,
        )
        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_notifications_agent_agent_creates_2_notifications(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value={"id": "rn:1"})
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, surreal)

        received = []

        async def callback(notif):
            received.append(notif)

        service.register_notification_callback(callback)
        event = make_event(relationship_type="agent_agent", party_b="max")

        await service._create_and_send_notifications(
            relationship_type="agent_agent",
            party_a="lisa",
            party_b="max",
            old_status=RelationshipStatus.STRANGER,
            new_status=RelationshipStatus.FRIEND,
            old_score=10.0,
            new_score=60.0,
            change_magnitude=ChangeMagnitude.MAJOR,
            event=event,
        )
        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_callback_exception_swallowed(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value={"id": "rn:1"})
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, surreal)

        async def failing_callback(notif):
            raise ValueError("callback error")

        service.register_notification_callback(failing_callback)
        event = make_event()

        await service._create_and_send_notifications(
            relationship_type="agent_user",
            party_a="lisa",
            party_b="user123",
            old_status=RelationshipStatus.STRANGER,
            new_status=RelationshipStatus.FRIEND,
            old_score=10.0,
            new_score=60.0,
            change_magnitude=ChangeMagnitude.MAJOR,
            event=event,
        )

    @pytest.mark.asyncio
    async def test_notifications_unknown_relationship_type_no_recipients(self):
        surreal = make_surreal()
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, surreal)
        event = make_event(relationship_type="other")

        received = []

        async def callback(notif):
            received.append(notif)

        service.register_notification_callback(callback)

        await service._create_and_send_notifications(
            relationship_type="other",
            party_a="lisa",
            party_b="user123",
            old_status=None,
            new_status=RelationshipStatus.FRIEND,
            old_score=0.0,
            new_score=60.0,
            change_magnitude=ChangeMagnitude.MAJOR,
            event=event,
        )
        assert received == []


class TestSocialGridServiceRecordInteractions:
    @pytest.mark.asyncio
    async def test_record_agent_user_interaction_with_service(self):
        mock_redis = AsyncMock()
        surreal = make_surreal()
        service = SocialGridService(mock_redis, surreal)

        from features.home.user_relationships.models import UserRelationship, InteractionType

        mock_relationship = UserRelationship(agent_id="lisa", user_id="user123")
        mock_relationship.score = 60.0
        mock_relationship.status = RelationshipStatus.FRIEND

        mock_user_svc = MagicMock()
        mock_user_svc.record_interaction = AsyncMock(return_value=mock_relationship)
        mock_user_svc.get_all_relationships = AsyncMock(return_value=[mock_relationship])
        mock_user_svc.repository = MagicMock()
        mock_user_svc.repository.redis = MagicMock(spec=[])

        service.set_user_relationship_service(mock_user_svc)

        result = await service.record_agent_user_interaction(
            agent_id="lisa",
            user_id="user123",
            interaction_type=InteractionType.HELPFUL,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_record_agent_agent_interaction_with_service(self):
        mock_redis = AsyncMock()
        surreal = make_surreal()
        service = SocialGridService(mock_redis, surreal)

        from features.home.agent_relationships.models import AgentRelationship, InteractionType as AgentInteractionType

        mock_relationship = AgentRelationship(agent_a="lisa", agent_b="max")
        mock_relationship.score = 50.0
        mock_relationship.status = RelationshipStatus.FRIEND

        mock_agent_svc = MagicMock()
        mock_agent_svc.record_interaction = AsyncMock(return_value=mock_relationship)
        mock_agent_svc.get_all_relationships = AsyncMock(return_value=[mock_relationship])

        service.set_agent_relationship_service(mock_agent_svc)

        result = await service.record_agent_agent_interaction(
            agent_a="lisa",
            agent_b="max",
            interaction_type=AgentInteractionType.COLLABORATIVE,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_record_agent_agent_interaction_with_service(self):
        mock_redis = AsyncMock()
        surreal = make_surreal()
        service = SocialGridService(mock_redis, surreal)

        from features.home.agent_relationships.models import AgentRelationship, InteractionType as AgentInteractionType

        mock_relationship = AgentRelationship(agent_a="lisa", agent_b="max")
        mock_relationship.score = 50.0
        mock_relationship.status = RelationshipStatus.FRIEND

        mock_agent_svc = MagicMock()
        mock_agent_svc.record_interaction = AsyncMock(return_value=mock_relationship)
        mock_agent_svc.get_all_relationships = AsyncMock(return_value=[mock_relationship])

        service.set_agent_relationship_service(mock_agent_svc)

        result = await service.record_agent_agent_interaction(
            agent_a="lisa",
            agent_b="max",
            interaction_type=AgentInteractionType.COLLABORATIVE,
        )
        assert result is not None


class TestSocialGridServiceOtherMethods:
    @pytest.mark.asyncio
    async def test_mark_notification_read_decrements(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        service._state.pending_notifications = 3
        service.repository.mark_notification_read = AsyncMock(return_value=True)
        result = await service.mark_notification_read("notif-1")
        assert result is True
        assert service._state.pending_notifications == 2

    @pytest.mark.asyncio
    async def test_mark_notification_read_false_no_decrement(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        service._state.pending_notifications = 1
        service.repository.mark_notification_read = AsyncMock(return_value=False)
        result = await service.mark_notification_read("notif-1")
        assert result is False
        assert service._state.pending_notifications == 1

    @pytest.mark.asyncio
    async def test_mark_notification_read_no_go_below_zero(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        service._state.pending_notifications = 0
        service.repository.mark_notification_read = AsyncMock(return_value=True)
        await service.mark_notification_read("notif-1")
        assert service._state.pending_notifications == 0

    @pytest.mark.asyncio
    async def test_get_unread_count(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        service.repository.get_unread_count = AsyncMock(return_value=7)
        count = await service.get_unread_count("user123")
        assert count == 7

    @pytest.mark.asyncio
    async def test_get_recent_events(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        service.repository.get_recent_events = AsyncMock(return_value=[make_event()])
        events = await service.get_recent_events(relationship_type="agent_user")
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_persist_state(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        service.repository.save_grid_state = AsyncMock(return_value=True)
        result = await service.persist_state()
        assert result is True

    @pytest.mark.asyncio
    async def test_get_agent_relationships_with_service(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        mock_agent_svc = AsyncMock()
        mock_agent_svc.get_all_relationships = AsyncMock(return_value=["rel1"])
        service.set_agent_relationship_service(mock_agent_svc)
        result = await service.get_agent_relationships("lisa")
        assert result == ["rel1"]

    @pytest.mark.asyncio
    async def test_get_agent_relationships_no_service(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        result = await service.get_agent_relationships("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_relationships_with_service(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        mock_user_svc = AsyncMock()
        mock_user_svc.get_all_relationships = AsyncMock(return_value=["rel1", "rel2"])
        service.set_user_relationship_service(mock_user_svc)
        result = await service.get_user_relationships("lisa")
        assert result == ["rel1", "rel2"]

    @pytest.mark.asyncio
    async def test_get_user_relationships_no_service(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        result = await service.get_user_relationships("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_initialize_with_surreal_loads_state(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=[{"result": [{"agent_user_relationships_count": 2}]}])
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, surreal)
        await service.initialize()
        assert service._initialized is True
        assert service._state.loaded_from_db is True

    @pytest.mark.asyncio
    async def test_initialize_twice_noop(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        await service.initialize()
        await service.initialize()
        assert service._initialized is True
