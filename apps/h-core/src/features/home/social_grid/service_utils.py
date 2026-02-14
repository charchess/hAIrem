from typing import Optional

from .models import (
    ChangeMagnitude,
    NotificationType,
)
from .models import INTERACTION_SCORES as USER_INTERACTION_SCORES
from ..agent_relationships.models import INTERACTION_SCORES as AGENT_INTERACTION_SCORES
from ..user_relationships.models import RelationshipStatus


SIGNIFICANT_SCORE_CHANGE = 20
MAJOR_SCORE_CHANGE = 40
CRITICAL_SCORE_CHANGE = 60


def calculate_change_magnitude(old_score: float, new_score: float) -> ChangeMagnitude:
    score_diff = abs(new_score - old_score)

    if score_diff >= CRITICAL_SCORE_CHANGE:
        return ChangeMagnitude.CRITICAL
    elif score_diff >= MAJOR_SCORE_CHANGE:
        return ChangeMagnitude.MAJOR
    elif score_diff >= SIGNIFICANT_SCORE_CHANGE:
        return ChangeMagnitude.MODERATE
    else:
        return ChangeMagnitude.MINOR


def get_notification_type(
    old_status: Optional[RelationshipStatus],
    new_status: RelationshipStatus,
    change_magnitude: ChangeMagnitude,
) -> NotificationType:
    if old_status is None:
        return NotificationType.NEW_RELATIONSHIP

    old_order = _get_status_order(old_status)
    new_order = _get_status_order(new_status)

    if new_order > old_order:
        return NotificationType.STATUS_UPGRADE
    elif new_order < old_order:
        return NotificationType.STATUS_DOWNGRADE
    elif change_magnitude in (ChangeMagnitude.MAJOR, ChangeMagnitude.CRITICAL):
        return NotificationType.SCORE_SIGNIFICANT_CHANGE
    else:
        return NotificationType.SCORE_SIGNIFICANT_CHANGE


def _get_status_order(status: RelationshipStatus) -> int:
    order = {
        RelationshipStatus.ENEMY: 0,
        RelationshipStatus.RIVAL: 1,
        RelationshipStatus.STRANGER: 2,
        RelationshipStatus.ACQUAINTANCE: 3,
        RelationshipStatus.FRIEND: 4,
        RelationshipStatus.ALLY: 5,
    }
    return order.get(status, 2)


def generate_notification_message(
    notification_type: NotificationType,
    recipient_type: str,
    party_a: str,
    party_b: str,
    old_status: Optional[RelationshipStatus],
    new_status: RelationshipStatus,
    old_score: float,
    new_score: float,
) -> str:
    if recipient_type == "agent":
        if notification_type == NotificationType.STATUS_UPGRADE:
            return f"Your relationship with {party_b} has improved to {new_status.value}!"
        elif notification_type == NotificationType.STATUS_DOWNGRADE:
            return f"Your relationship with {party_b} has degraded to {new_status.value}."
        elif notification_type == NotificationType.NEW_RELATIONSHIP:
            return f"You've formed a new relationship with {party_b}."
        elif notification_type == NotificationType.SCORE_SIGNIFICANT_CHANGE:
            return f"Your relationship score with {party_b} changed significantly ({old_score:.0f} -> {new_score:.0f})."
    else:
        if notification_type == NotificationType.STATUS_UPGRADE:
            return f"{party_a}'s attitude toward you has improved to {new_status.value}!"
        elif notification_type == NotificationType.STATUS_DOWNGRADE:
            return f"{party_a}'s attitude toward you has cooled to {new_status.value}."
        elif notification_type == NotificationType.NEW_RELATIONSHIP:
            return f"{party_a} has formed a relationship with you."
        elif notification_type == NotificationType.SCORE_SIGNIFICANT_CHANGE:
            return f"Your relationship score with {party_a} changed ({old_score:.0f} -> {new_score:.0f})."

    return "Your relationship has been updated."


def get_interaction_delta(interaction_type) -> float:
    if hasattr(interaction_type, 'value'):
        interaction_value = interaction_type.value
    else:
        interaction_value = str(interaction_type)

    return USER_INTERACTION_SCORES.get(interaction_value, AGENT_INTERACTION_SCORES.get(interaction_value, 0))
