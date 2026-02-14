import pytest
from unittest.mock import AsyncMock, MagicMock
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
    calculate_change_magnitude,
    generate_notification_message,
    get_notification_type,
)
from features.home.user_relationships import RelationshipStatus


class TestChangeMagnitude:
    def test_calculate_change_magnitude_minor(self):
        assert calculate_change_magnitude(10, 15) == ChangeMagnitude.MINOR
        assert calculate_change_magnitude(50, 55) == ChangeMagnitude.MINOR

    def test_calculate_change_magnitude_moderate(self):
        assert calculate_change_magnitude(10, 35) == ChangeMagnitude.MODERATE
        assert calculate_change_magnitude(50, 30) == ChangeMagnitude.MODERATE

    def test_calculate_change_magnitude_major(self):
        assert calculate_change_magnitude(10, 60) == ChangeMagnitude.MAJOR
        assert calculate_change_magnitude(50, 10) == ChangeMagnitude.MAJOR

    def test_calculate_change_magnitude_critical(self):
        assert calculate_change_magnitude(10, 80) == ChangeMagnitude.CRITICAL
        assert calculate_change_magnitude(50, -30) == ChangeMagnitude.CRITICAL


class TestNotificationType:
    def test_get_notification_type_new_relationship(self):
        result = get_notification_type(None, RelationshipStatus.STRANGER, ChangeMagnitude.MINOR)
        assert result == NotificationType.NEW_RELATIONSHIP

    def test_get_notification_type_upgrade(self):
        result = get_notification_type(
            RelationshipStatus.STRANGER,
            RelationshipStatus.FRIEND,
            ChangeMagnitude.MINOR
        )
        assert result == NotificationType.STATUS_UPGRADE

    def test_get_notification_type_downgrade(self):
        result = get_notification_type(
            RelationshipStatus.FRIEND,
            RelationshipStatus.RIVAL,
            ChangeMagnitude.MINOR
        )
        assert result == NotificationType.STATUS_DOWNGRADE


class TestNotificationMessage:
    def test_generate_message_status_upgrade_agent(self):
        msg = generate_notification_message(
            notification_type=NotificationType.STATUS_UPGRADE,
            recipient_type="agent",
            party_a="lisa",
            party_b="user123",
            old_status=RelationshipStatus.STRANGER,
            new_status=RelationshipStatus.FRIEND,
            old_score=10,
            new_score=60,
        )
        assert "improved" in msg
        assert "friend" in msg

    def test_generate_message_status_downgrade_agent(self):
        msg = generate_notification_message(
            notification_type=NotificationType.STATUS_DOWNGRADE,
            recipient_type="agent",
            party_a="lisa",
            party_b="user123",
            old_status=RelationshipStatus.FRIEND,
            new_status=RelationshipStatus.RIVAL,
            old_score=60,
            new_score=-40,
        )
        assert "degraded" in msg
        assert "rival" in msg


class TestRelationshipChangeEvent:
    def test_to_dict(self):
        event = RelationshipChangeEvent(
            relationship_type="agent_user",
            party_a="lisa",
            party_b="user123",
            old_status="stranger",
            new_status="friend",
            old_score=10,
            new_score=60,
            change_magnitude=ChangeMagnitude.MAJOR,
        )

        data = event.to_dict()
        assert data["relationship_type"] == "agent_user"
        assert data["party_a"] == "lisa"
        assert data["new_status"] == "friend"
        assert data["change_magnitude"] == "major"

    def test_from_dict(self):
        data = {
            "relationship_type": "agent_user",
            "party_a": "lisa",
            "party_b": "user123",
            "old_status": "stranger",
            "new_status": "friend",
            "old_score": 10,
            "new_score": 60,
            "change_magnitude": "major",
            "timestamp": "2024-01-15T10:30:00",
        }

        event = RelationshipChangeEvent.from_dict(data)
        assert event.relationship_type == "agent_user"
        assert event.new_status == "friend"
        assert event.change_magnitude == ChangeMagnitude.MAJOR


class TestRelationshipNotification:
    def test_to_dict(self):
        event = RelationshipChangeEvent(
            relationship_type="agent_user",
            party_a="lisa",
            party_b="user123",
            old_status="stranger",
            new_status="friend",
            old_score=10,
            new_score=60,
            change_magnitude=ChangeMagnitude.MAJOR,
        )

        notification = RelationshipNotification(
            notification_type=NotificationType.STATUS_UPGRADE,
            recipient_id="lisa",
            recipient_type="agent",
            event=event,
            message="Your relationship has improved!",
        )

        data = notification.to_dict()
        assert data["notification_type"] == "status_upgrade"
        assert data["recipient_id"] == "lisa"
        assert data["event"]["new_status"] == "friend"


class TestSocialGridState:
    def test_to_dict(self):
        state = SocialGridState(
            agent_user_relationships_count=10,
            agent_agent_relationships_count=5,
            pending_notifications=3,
            last_evolution_timestamp=datetime.utcnow(),
            loaded_from_db=True,
        )

        data = state.to_dict()
        assert data["agent_user_relationships_count"] == 10
        assert data["loaded_from_db"] is True


class TestSocialGridRepository:
    @pytest.mark.asyncio
    async def test_setup_schema_no_surreal(self):
        repo = SocialGridRepository(None)
        await repo.setup_schema()

    @pytest.mark.asyncio
    async def test_save_relationship_event_no_surreal(self):
        repo = SocialGridRepository(None)
        event = RelationshipChangeEvent(
            relationship_type="agent_user",
            party_a="lisa",
            party_b="user123",
            old_status="stranger",
            new_status="friend",
            old_score=10,
            new_score=60,
            change_magnitude=ChangeMagnitude.MAJOR,
        )
        result = await repo.save_relationship_event(event)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_recent_events_no_surreal(self):
        repo = SocialGridRepository(None)
        events = await repo.get_recent_events()
        assert events == []


class TestSocialGridService:
    @pytest.mark.asyncio
    async def test_initialize(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        await service.initialize()
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_get_state(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        await service.initialize()
        state = await service.get_state()
        assert isinstance(state, SocialGridState)

    @pytest.mark.asyncio
    async def test_record_agent_user_interaction_no_service(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        await service.initialize()

        result = await service.record_agent_user_interaction(
            agent_id="lisa",
            user_id="user123",
            interaction_type="helpful",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_record_agent_agent_interaction_no_service(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        await service.initialize()

        result = await service.record_agent_agent_interaction(
            agent_a="lisa",
            agent_b="max",
            interaction_type="collaborative",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_notifications_no_surreal(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)
        await service.initialize()

        notifications = await service.get_notifications("user123")
        assert notifications == []

    @pytest.mark.asyncio
    async def test_notification_callback(self):
        mock_redis = AsyncMock()
        service = SocialGridService(mock_redis, None)

        callback_called = []

        async def test_callback(notification):
            callback_called.append(True)

        service.register_notification_callback(test_callback)
        assert len(service._notification_callbacks) == 1
