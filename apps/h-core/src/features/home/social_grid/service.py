import asyncio
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, List, Optional

from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient

from .models import (
    ChangeMagnitude,
    RelationshipChangeEvent,
    RelationshipNotification,
    SocialGridState,
)
from .repository import SocialGridRepository
from .service_utils import (
    calculate_change_magnitude,
    generate_notification_message,
    get_notification_type,
)
from ..user_relationships.models import RelationshipStatus

logger = logging.getLogger(__name__)

NotificationCallback = Callable[[RelationshipNotification], Awaitable[None]]


class SocialGridService:
    def __init__(
        self,
        redis_client: RedisClient,
        surreal_client: Optional[SurrealDbClient] = None,
    ):
        self.redis = redis_client
        self.surreal = surreal_client
        self.repository = SocialGridRepository(surreal_client)
        self._notification_callbacks: List[NotificationCallback] = []
        self._state = SocialGridState()
        self._initialized = False
        self._user_relationship_service = None
        self._agent_relationship_service = None

    def set_user_relationship_service(self, service):
        self._user_relationship_service = service

    def set_agent_relationship_service(self, service):
        self._agent_relationship_service = service

    def register_notification_callback(self, callback: NotificationCallback):
        self._notification_callbacks.append(callback)

    async def initialize(self):
        if self._initialized:
            return

        await self.repository.setup_schema()
        await self._load_from_surreal()
        self._initialized = True
        logger.info("Social grid initialized")

    async def _load_from_surreal(self):
        if not self.surreal or not self.surreal.client:
            logger.info("SurrealDB not available, using Redis only")
            return

        state_data = await self.repository.load_grid_state()
        if state_data:
            self._state.loaded_from_db = True
            logger.info("Social grid state loaded from SurrealDB")

    async def _notify_change(
        self,
        relationship_type: str,
        party_a: str,
        party_b: str,
        old_status: Optional[RelationshipStatus],
        new_status: RelationshipStatus,
        old_score: float,
        new_score: float,
    ) -> Optional[RelationshipChangeEvent]:
        if old_status == new_status and abs(new_score - old_score) < 20:
            return None

        change_magnitude = calculate_change_magnitude(old_score, new_score)
        if change_magnitude == ChangeMagnitude.MINOR:
            return None

        event = RelationshipChangeEvent(
            relationship_type=relationship_type,
            party_a=party_a,
            party_b=party_b,
            old_status=old_status.value if old_status else None,
            new_status=new_status.value,
            old_score=old_score,
            new_score=new_score,
            change_magnitude=change_magnitude,
        )

        await self.repository.save_relationship_event(event)
        self._state.last_evolution_timestamp = datetime.utcnow()

        await self._create_and_send_notifications(
            relationship_type=relationship_type,
            party_a=party_a,
            party_b=party_b,
            old_status=old_status,
            new_status=new_status,
            old_score=old_score,
            new_score=new_score,
            change_magnitude=change_magnitude,
            event=event,
        )

        return event

    async def _create_and_send_notifications(
        self,
        relationship_type: str,
        party_a: str,
        party_b: str,
        old_status: Optional[RelationshipStatus],
        new_status: RelationshipStatus,
        old_score: float,
        new_score: float,
        change_magnitude: ChangeMagnitude,
        event: RelationshipChangeEvent,
    ):
        notification_type = get_notification_type(old_status, new_status, change_magnitude)

        recipients = []
        if relationship_type == "agent_user":
            recipients = [
                {"id": party_a, "type": "agent"},
                {"id": party_b, "type": "user"},
            ]
        elif relationship_type == "agent_agent":
            recipients = [
                {"id": party_a, "type": "agent"},
                {"id": party_b, "type": "agent"},
            ]

        for recipient in recipients:
            message = generate_notification_message(
                notification_type=notification_type,
                recipient_type=recipient["type"],
                party_a=party_a,
                party_b=party_b,
                old_status=old_status,
                new_status=new_status,
                old_score=old_score,
                new_score=new_score,
            )

            notification = RelationshipNotification(
                notification_type=notification_type,
                recipient_id=recipient["id"],
                recipient_type=recipient["type"],
                event=event,
                message=message,
            )

            await self.repository.save_notification(notification)
            self._state.pending_notifications += 1

            for callback in self._notification_callbacks:
                try:
                    await callback(notification)
                except Exception as e:
                    logger.error(f"Notification callback failed: {e}")

    async def record_agent_user_interaction(
        self,
        agent_id: str,
        user_id: str,
        interaction_type,
        context: str = "",
    ) -> Any:
        if not self._user_relationship_service:
            logger.warning("User relationship service not set")
            return None

        relationship = await self._user_relationship_service.record_interaction(
            agent_id=agent_id,
            user_id=user_id,
            interaction_type=interaction_type,
            context=context,
        )

        old_status = relationship.status
        old_score = relationship.score - (
            self._user_relationship_service.repository.redis._get_interaction_delta(interaction_type)
            if hasattr(self._user_relationship_service.repository.redis, '_get_interaction_delta')
            else 0
        )

        from .service_utils import get_interaction_delta
        old_score = relationship.score - get_interaction_delta(interaction_type)

        await self._notify_change(
            relationship_type="agent_user",
            party_a=agent_id,
            party_b=user_id,
            old_status=None,
            new_status=relationship.status,
            old_score=max(-100, old_score),
            new_score=relationship.score,
        )

        await self._update_counts()
        return relationship

    async def record_agent_agent_interaction(
        self,
        agent_a: str,
        agent_b: str,
        interaction_type,
        context: str = "",
    ) -> Any:
        if not self._agent_relationship_service:
            logger.warning("Agent relationship service not set")
            return None

        relationship = await self._agent_relationship_service.record_interaction(
            agent_a=agent_a,
            agent_b=agent_b,
            interaction_type=interaction_type,
            context=context,
        )

        from .service_utils import get_interaction_delta
        old_score = relationship.score - get_interaction_delta(interaction_type)

        await self._notify_change(
            relationship_type="agent_agent",
            party_a=agent_a,
            party_b=agent_b,
            old_status=None,
            new_status=relationship.status,
            old_score=max(-100, old_score),
            new_score=relationship.score,
        )

        await self._update_counts()
        return relationship

    async def _update_counts(self):
        if self._user_relationship_service:
            user_rels = await self._user_relationship_service.get_all_relationships("__all__")
            self._state.agent_user_relationships_count = len(user_rels)

        if self._agent_relationship_service:
            agent_rels = await self._agent_relationship_service.get_all_relationships("__all__")
            self._state.agent_agent_relationships_count = len(agent_rels)

    async def get_notifications(
        self,
        recipient_id: str,
        unread_only: bool = False,
    ) -> List[RelationshipNotification]:
        return await self.repository.get_notifications_for_recipient(
            recipient_id=recipient_id,
            unread_only=unread_only,
        )

    async def mark_notification_read(self, notification_id: str) -> bool:
        result = await self.repository.mark_notification_read(notification_id)
        if result:
            self._state.pending_notifications = max(0, self._state.pending_notifications - 1)
        return result

    async def get_unread_count(self, recipient_id: str) -> int:
        return await self.repository.get_unread_count(recipient_id)

    async def get_recent_events(
        self,
        relationship_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[RelationshipChangeEvent]:
        return await self.repository.get_recent_events(
            relationship_type=relationship_type,
            limit=limit,
        )

    async def get_state(self) -> SocialGridState:
        await self._update_counts()
        return self._state

    async def persist_state(self) -> bool:
        state_data = self._state.to_dict()
        return await self.repository.save_grid_state(state_data)

    async def get_agent_relationships(self, agent_id: str) -> List[Any]:
        if self._agent_relationship_service:
            return await self._agent_relationship_service.get_all_relationships(agent_id)
        return []

    async def get_user_relationships(self, agent_id: str) -> List[Any]:
        if self._user_relationship_service:
            return await self._user_relationship_service.get_all_relationships(agent_id)
        return []
