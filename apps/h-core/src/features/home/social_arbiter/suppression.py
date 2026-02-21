import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SuppressionReason(Enum):
    LOW_RELEVANCE_SCORE = "low_relevance_score"
    BELOW_THRESHOLD = "below_threshold"
    SUPERSEDED = "superseded"


@dataclass
class SuppressionConfig:
    minimum_threshold: float = 0.15
    enable_suppression: bool = True
    enable_reevaluation: bool = True
    reevaluation_delay_seconds: float = 30.0
    max_reevaluation_attempts: int = 3
    context_change_weight: float = 0.3


@dataclass
class SuppressedResponse:
    agent_id: str
    message_content: str
    score: float
    reason: SuppressionReason
    timestamp: datetime = field(default_factory=datetime.now)
    reevaluation_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def can_reevaluate(self, config: SuppressionConfig) -> bool:
        if not config.enable_reevaluation:
            return False
        if self.reevaluation_count >= config.max_reevaluation_attempts:
            return False
        return True

    def should_reevaluate(self, config: SuppressionConfig) -> bool:
        if not self.can_reevaluate(config):
            return False
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed >= config.reevaluation_delay_seconds


class SuppressionLogger:
    def __init__(self):
        self._suppression_history: list[SuppressedResponse] = []
        self._suppression_count_by_agent: dict[str, int] = {}
        self._suppression_count_by_reason: dict[SuppressionReason, int] = {}

    def log_suppression(self, response: SuppressedResponse) -> None:
        self._suppression_history.append(response)

        self._suppression_count_by_agent[response.agent_id] = (
            self._suppression_count_by_agent.get(response.agent_id, 0) + 1
        )

        self._suppression_count_by_reason[response.reason] = (
            self._suppression_count_by_reason.get(response.reason, 0) + 1
        )

        logger.warning(
            f"Response suppressed: agent={response.agent_id}, "
            f"score={response.score:.3f}, reason={response.reason.value}, "
            f"message={response.message_content[:50]}..."
        )

    def get_suppression_stats(self) -> dict[str, Any]:
        return {
            "total_suppressions": len(self._suppression_history),
            "by_agent": dict(self._suppression_count_by_agent),
            "by_reason": {k.value: v for k, v in self._suppression_count_by_reason.items()},
            "recent_suppressions": len(
                [s for s in self._suppression_history if (datetime.now() - s.timestamp).total_seconds() < 3600]
            ),
        }

    def get_suppression_history(self, limit: int = 100) -> list[dict[str, Any]]:
        history = sorted(self._suppression_history, key=lambda x: x.timestamp, reverse=True)
        return [
            {
                "agent_id": s.agent_id,
                "score": s.score,
                "reason": s.reason.value,
                "timestamp": s.timestamp.isoformat(),
                "reevaluation_count": s.reevaluation_count,
                "message_preview": s.message_content[:50],
            }
            for s in history[:limit]
        ]

    def clear_history(self) -> None:
        self._suppression_history.clear()
        self._suppression_count_by_agent.clear()
        self._suppression_count_by_reason.clear()


class ResponseSuppressor:
    def __init__(self, config: SuppressionConfig | None = None):
        self.config = config or SuppressionConfig()
        self.suppression_logger = SuppressionLogger()
        self._delayed_queue: list[SuppressedResponse] = []
        self._last_spoke_times: dict[str, float] = {}

    def record_speech(self, agent_id: str) -> None:
        """Records the time an agent spoke."""
        self._last_spoke_times[agent_id] = time.time()

    def get_time_since_last_spoke(self, agent_id: str) -> float:
        """Returns seconds since agent last spoke."""
        last_time = self._last_spoke_times.get(agent_id, 0)
        if last_time == 0:
            return 999999.0
        return time.time() - last_time

    def should_suppress(self, agent_id: str, score: float) -> bool:
        if not self.config.enable_suppression:
            return False
        return score < self.config.minimum_threshold

    def suppress_response(
        self,
        agent_id: str,
        message_content: str,
        score: float,
        reason: SuppressionReason = SuppressionReason.BELOW_THRESHOLD,
        metadata: dict[str, Any] | None = None,
    ) -> SuppressedResponse | None:
        if not self.should_suppress(agent_id, score):
            return None

        suppressed = SuppressedResponse(
            agent_id=agent_id,
            message_content=message_content,
            score=score,
            reason=reason,
            metadata=metadata or {},
        )

        self.suppression_logger.log_suppression(suppressed)

        if self.config.enable_reevaluation:
            self._delayed_queue.append(suppressed)

        return suppressed

    def get_pending_reevaluations(self) -> list[SuppressedResponse]:
        pending = []
        remaining = []

        for suppressed in self._delayed_queue:
            if suppressed.should_reevaluate(self.config):
                suppressed.reevaluation_count += 1
                pending.append(suppressed)
            else:
                remaining.append(suppressed)

        self._delayed_queue = remaining
        return pending

    def get_queue_size(self) -> int:
        return len(self._delayed_queue)

    def clear_queue(self) -> int:
        count = len(self._delayed_queue)
        self._delayed_queue.clear()
        return count

    def get_stats(self) -> dict[str, Any]:
        base_stats = self.suppression_logger.get_suppression_stats()
        base_stats["delayed_queue_size"] = self.get_queue_size()
        return base_stats

    def check_context_change(
        self,
        suppressed: SuppressedResponse,
        current_context: dict[str, Any],
    ) -> float:
        previous_context = suppressed.metadata.get("context", {})

        if not previous_context:
            return 0.0

        change_score = 0.0

        if "emotional_context" in current_context:
            current_emotion = current_context.get("emotional_context", {}).get("primary_emotion")
            prev_emotion = previous_context.get("emotional_context", {}).get("primary_emotion")
            if current_emotion and prev_emotion and current_emotion != prev_emotion:
                change_score += self.config.context_change_weight

        if "mentioned_agents" in current_context:
            current_mentioned = set(current_context.get("mentioned_agents", []))
            prev_mentioned = set(previous_context.get("mentioned_agents", []))
            if current_mentioned != prev_mentioned:
                change_score += self.config.context_change_weight

        return min(change_score, 1.0)
