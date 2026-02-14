import logging
from datetime import datetime
from typing import Any, Optional

from features.home.social_arbiter.emotion_detection import EmotionDetector
from features.home.emotional_history.models import EmotionalStateRecord, EmotionalSummary
from features.home.emotional_history.repository import EmotionalHistoryRepository

logger = logging.getLogger(__name__)

DEFAULT_EMOTION_LIMIT = 10
SUMMARY_THRESHOLD = 20


class EmotionalHistoryService:
    def __init__(
        self,
        redis_client: Any = None,
        emotion_detector: Optional[EmotionDetector] = None,
    ):
        self.repository = EmotionalHistoryRepository(redis_client)
        self.emotion_detector = emotion_detector or EmotionDetector()

    async def detect_and_store_emotion(
        self,
        user_id: str,
        message: str,
        agent_id: str = "system",
    ) -> Optional[EmotionalStateRecord]:
        context = self.emotion_detector.detect_emotions(message)
        
        if not context.primary_emotion:
            return None

        record = EmotionalStateRecord(
            emotion=context.primary_emotion,
            intensity=context.overall_intensity,
            keywords=[e.keywords[0] for e in context.detected_emotions[:3]],
            context=message[:200],
            user_id=user_id,
            agent_id=agent_id,
        )

        await self.repository.store_emotional_state(
            user_id=user_id,
            emotion=record.emotion,
            intensity=record.intensity,
            context=record.context,
            keywords=record.keywords,
            agent_id=agent_id,
        )

        await self._check_and_archive(user_id)

        return record

    async def get_emotional_context(
        self,
        user_id: str,
        limit: int = DEFAULT_EMOTION_LIMIT,
    ) -> dict[str, Any]:
        recent = await self.repository.get_recent_emotions(user_id, limit)
        
        if not recent:
            return {
                "has_history": False,
                "recent_emotions": [],
                "current_emotion": None,
                "current_intensity": 0.0,
            }

        current = recent[0]
        
        emotion_counts: dict[str, int] = {}
        total_intensity = 0.0
        for r in recent:
            emotion = r.get("emotion", "neutral")
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_intensity += r.get("intensity", 0.0)

        return {
            "has_history": True,
            "recent_emotions": recent,
            "current_emotion": current.get("emotion"),
            "current_intensity": current.get("intensity"),
            "emotion_counts": emotion_counts,
            "average_intensity": total_intensity / len(recent),
            "context_length": len(recent),
        }

    async def _check_and_archive(self, user_id: str) -> bool:
        recent = await self.repository.get_recent_emotions(user_id, SUMMARY_THRESHOLD + 1)
        
        if len(recent) < SUMMARY_THRESHOLD:
            return False

        to_archive = recent[:SUMMARY_THRESHOLD]
        remaining = recent[SUMMARY_THRESHOLD:]

        summary = self._create_summary(user_id, to_archive)
        
        await self.repository.archive_emotions(user_id, summary.to_dict())
        
        redis_client = self.repository.redis
        if redis_client and redis_client.client:
            key = f"emotional_history:{user_id}"
            for _ in range(SUMMARY_THRESHOLD):
                await redis_client.client.lpop(key)
            for r in remaining:
                await redis_client.client.rpush(key, r)

        logger.info(f"Archived {SUMMARY_THRESHOLD} emotional records for user {user_id}")
        return True

    def _create_summary(
        self,
        user_id: str,
        records: list[dict[str, Any]],
    ) -> EmotionalSummary:
        emotion_counts: dict[str, int] = {}
        total_intensity = 0.0
        
        for r in records:
            emotion = r.get("emotion", "neutral")
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_intensity += r.get("intensity", 0.0)

        timestamps = []
        for r in records:
            ts = r.get("timestamp")
            if ts:
                try:
                    timestamps.append(datetime.fromisoformat(ts))
                except:
                    pass

        period_start = min(timestamps) if timestamps else datetime.utcnow()
        period_end = max(timestamps) if timestamps else datetime.utcnow()
        
        dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"
        avg_intensity = total_intensity / len(records) if records else 0.0

        emotion_percentages = {e: (c / len(records) * 100) for e, c in emotion_counts.items()}
        summary_parts = [f"{e}: {p:.0f}%" for e, p in sorted(emotion_percentages.items(), key=lambda x: -x[1])[:3]]
        summary_text = f"User expressed {dominant_emotion} as dominant emotion. Distribution: {', '.join(summary_parts)}"

        return EmotionalSummary(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            emotion_counts=emotion_counts,
            dominant_emotion=dominant_emotion,
            average_intensity=avg_intensity,
            summary_text=summary_text,
        )

    async def get_full_context(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        emotional_context = await self.get_emotional_context(user_id)
        
        archived = await self.repository.get_archived_summaries(user_id, limit=5)
        
        emotional_context["archived_summaries"] = archived
        emotional_context["total_archived"] = len(archived)

        return emotional_context
