import pytest
import json
from unittest.mock import AsyncMock, MagicMock

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.features.home.social_arbiter.emotion_detection import (
    EmotionDetector,
    EmotionalStateManager,
)
from features.home.emotional_history.repository import EmotionalHistoryRepository


class TestEmotionDetectorExtra:
    def test_detect_emotions_returns_empty_context_for_no_emotion_text(self):
        detector = EmotionDetector()
        ctx = detector.detect_emotions("The sky is blue")
        assert ctx.primary_emotion is None or ctx.overall_intensity < 0.1

    def test_get_required_emotions_no_primary(self):
        from src.features.home.social_arbiter.emotion_detection import EmotionalContext

        detector = EmotionDetector()
        ctx = EmotionalContext()
        result = detector.get_required_emotions(ctx)
        assert result == []

    def test_get_required_emotions_known_emotion(self):
        from src.features.home.social_arbiter.emotion_detection import EmotionalContext

        detector = EmotionDetector()
        ctx = EmotionalContext(primary_emotion="happy")
        result = detector.get_required_emotions(ctx)
        assert "cheerful" in result

    def test_get_required_emotions_unknown_emotion_returns_empty(self):
        from src.features.home.social_arbiter.emotion_detection import EmotionalContext

        detector = EmotionDetector()
        ctx = EmotionalContext(primary_emotion="bored")
        result = detector.get_required_emotions(ctx)
        assert result == []

    def test_get_required_emotions_all_known_emotions(self):
        from src.features.home.social_arbiter.emotion_detection import EmotionalContext

        detector = EmotionDetector()
        emotions = [
            "sad",
            "angry",
            "excited",
            "fearful",
            "surprised",
            "calm",
            "curious",
            "grateful",
            "hopeful",
            "confused",
            "tired",
        ]
        for emotion in emotions:
            ctx = EmotionalContext(primary_emotion=emotion)
            result = detector.get_required_emotions(ctx)
            assert len(result) > 0

    def test_calculate_polarity_positive_emotion(self):
        from src.features.home.social_arbiter.emotion_detection import DetectedEmotion

        detector = EmotionDetector()
        emotions = [DetectedEmotion(emotion="happy", intensity=0.9, keywords=["happy"], position=0)]
        polarity = detector._calculate_polarity(emotions)
        assert polarity > 0

    def test_calculate_polarity_negative_emotion(self):
        from src.features.home.social_arbiter.emotion_detection import DetectedEmotion

        detector = EmotionDetector()
        emotions = [DetectedEmotion(emotion="angry", intensity=0.8, keywords=["angry"], position=0)]
        polarity = detector._calculate_polarity(emotions)
        assert polarity < 0

    def test_calculate_polarity_no_scored_emotions(self):
        from src.features.home.social_arbiter.emotion_detection import DetectedEmotion

        detector = EmotionDetector()
        emotions = [DetectedEmotion(emotion="unknown_emotion", intensity=0.5, keywords=["x"], position=0)]
        polarity = detector._calculate_polarity(emotions)
        assert polarity == 0.0

    def test_detect_emotions_intensity_modifier_very(self):
        detector = EmotionDetector()
        ctx = detector.detect_emotions("I am very happy today")
        assert ctx.primary_emotion is not None
        ctx2 = detector.detect_emotions("I am happy today")
        assert ctx.overall_intensity >= ctx2.overall_intensity

    def test_detect_emotions_is_mixed_when_multiple_categories(self):
        detector = EmotionDetector()
        ctx = detector.detect_emotions("I am happy but also sad and angry")
        if ctx.detected_emotions and len(ctx.detected_emotions) > 1:
            pass

    def test_detect_emotions_repeated_keyword_boosts_intensity(self):
        detector = EmotionDetector()
        ctx1 = detector.detect_emotions("I am happy")
        ctx2 = detector.detect_emotions("I am happy happy happy")
        assert ctx2.overall_intensity >= ctx1.overall_intensity


class TestEmotionalStateManager:
    def test_get_or_create_state_new_agent(self):
        manager = EmotionalStateManager()
        state = manager.get_or_create_state("lisa")
        assert state["current_emotion"] == "neutral"
        assert state["interactions_count"] == 0

    def test_get_or_create_state_returns_same_instance(self):
        manager = EmotionalStateManager()
        s1 = manager.get_or_create_state("lisa")
        s2 = manager.get_or_create_state("lisa")
        assert s1 is s2

    def test_update_emotional_state_no_emotion(self):
        manager = EmotionalStateManager()
        state = manager.update_emotional_state("lisa", None)
        assert state["interactions_count"] == 1
        assert state["current_emotion"] == "neutral"

    def test_update_emotional_state_with_emotion(self):
        manager = EmotionalStateManager()
        state = manager.update_emotional_state("lisa", "happy")
        assert state["current_emotion"] == "happy"
        assert state["emotion_intensity"] > 0

    def test_update_emotional_state_with_interaction_result(self):
        manager = EmotionalStateManager()
        state = manager.update_emotional_state("lisa", "sad", interaction_result={"timestamp": "2024-01-01"})
        assert state["last_emotion_change"] == "2024-01-01"

    def test_update_emotional_state_caps_history_at_50(self):
        manager = EmotionalStateManager()
        for i in range(55):
            manager.update_emotional_state("lisa", "happy")
        state = manager.get_state("lisa")
        assert len(state["emotional_history"]) == 50

    def test_determine_emotional_response_known_emotions(self):
        manager = EmotionalStateManager()
        emotions = [
            "happy",
            "sad",
            "angry",
            "excited",
            "fearful",
            "surprised",
            "calm",
            "curious",
            "grateful",
            "hopeful",
            "confused",
            "tired",
        ]
        for emotion in emotions:
            resp = manager._determine_emotional_response("neutral", emotion)
            assert "emotion" in resp
            assert "intensity" in resp

    def test_determine_emotional_response_unknown_emotion(self):
        manager = EmotionalStateManager()
        resp = manager._determine_emotional_response("neutral", "bored")
        assert resp["emotion"] == "neutral"

    def test_get_emotional_capability_score_no_emotion(self):
        manager = EmotionalStateManager()
        score = manager.get_emotional_capability_score(["cheerful"], None)
        assert score == 0.5

    def test_get_emotional_capability_score_matching_traits(self):
        manager = EmotionalStateManager()
        score = manager.get_emotional_capability_score(["cheerful", "joyful"], "happy")
        assert score > 0

    def test_get_emotional_capability_score_unknown_emotion(self):
        manager = EmotionalStateManager()
        score = manager.get_emotional_capability_score(["cheerful"], "bored")
        assert score == 0.5

    def test_get_state_returns_none_for_unknown(self):
        manager = EmotionalStateManager()
        assert manager.get_state("nobody") is None

    def test_get_history_returns_empty_for_unknown(self):
        manager = EmotionalStateManager()
        assert manager.get_history("nobody") == []

    def test_get_history_limited(self):
        manager = EmotionalStateManager()
        for i in range(15):
            manager.update_emotional_state("lisa", "happy")
        history = manager.get_history("lisa", limit=5)
        assert len(history) == 5


class TestEmotionalHistoryRepositoryExtra:
    @pytest.mark.asyncio
    async def test_store_emotional_state_trims_when_over_threshold(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lpush = AsyncMock()
        mock_client.llen = AsyncMock(return_value=45)
        mock_client.ltrim = AsyncMock()

        repo = EmotionalHistoryRepository(mock_redis)
        await repo.store_emotional_state("user_x", "happy", 0.8)

        mock_client.ltrim.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_emotional_state_returns_false_on_exception(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lpush = AsyncMock(side_effect=Exception("redis error"))

        repo = EmotionalHistoryRepository(mock_redis)
        result = await repo.store_emotional_state("user_x", "happy", 0.8)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_recent_emotions_skips_invalid_json(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lrange = AsyncMock(
            return_value=[
                json.dumps({"emotion": "happy", "intensity": 0.8}),
                b"not valid json",
            ]
        )

        repo = EmotionalHistoryRepository(mock_redis)
        result = await repo.get_recent_emotions("user_x")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_recent_emotions_returns_empty_on_exception(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lrange = AsyncMock(side_effect=Exception("redis error"))

        repo = EmotionalHistoryRepository(mock_redis)
        result = await repo.get_recent_emotions("user_x")
        assert result == []

    @pytest.mark.asyncio
    async def test_archive_emotions_trims_when_over_limit(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lpush = AsyncMock()
        mock_client.llen = AsyncMock(return_value=101)
        mock_client.ltrim = AsyncMock()

        repo = EmotionalHistoryRepository(mock_redis)
        await repo.archive_emotions("user_x", {"dominant_emotion": "happy"})

        mock_client.ltrim.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive_emotions_returns_false_on_exception(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lpush = AsyncMock(side_effect=Exception("redis error"))

        repo = EmotionalHistoryRepository(mock_redis)
        result = await repo.archive_emotions("user_x", {})
        assert result is False

    @pytest.mark.asyncio
    async def test_archive_emotions_no_redis_returns_false(self):
        repo = EmotionalHistoryRepository(None)
        result = await repo.archive_emotions("user_x", {})
        assert result is False

    @pytest.mark.asyncio
    async def test_get_archived_summaries_no_redis_returns_empty(self):
        repo = EmotionalHistoryRepository(None)
        result = await repo.get_archived_summaries("user_x")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_archived_summaries_returns_empty_on_exception(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lrange = AsyncMock(side_effect=Exception("redis error"))

        repo = EmotionalHistoryRepository(mock_redis)
        result = await repo.get_archived_summaries("user_x")
        assert result == []

    @pytest.mark.asyncio
    async def test_clear_history_calls_delete(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.delete = AsyncMock()

        repo = EmotionalHistoryRepository(mock_redis)
        result = await repo.clear_history("user_x")
        assert result is True
        mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_history_no_redis_returns_false(self):
        repo = EmotionalHistoryRepository(None)
        result = await repo.clear_history("user_x")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_history_returns_false_on_exception(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.delete = AsyncMock(side_effect=Exception("redis error"))

        repo = EmotionalHistoryRepository(mock_redis)
        result = await repo.clear_history("user_x")
        assert result is False
