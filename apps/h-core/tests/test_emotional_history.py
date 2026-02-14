import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from features.home.emotional_history import (
    EmotionalStateRecord,
    EmotionalSummary,
    EmotionalHistoryRepository,
    EmotionalHistoryService,
)


class TestEmotionalStateRecord:
    def test_to_dict(self):
        record = EmotionalStateRecord(
            emotion="happy",
            intensity=0.8,
            keywords=["happy", "joy"],
            context="I am so happy today!",
            user_id="user_123",
            agent_id="system",
        )
        
        data = record.to_dict()
        
        assert data["emotion"] == "happy"
        assert data["intensity"] == 0.8
        assert data["keywords"] == ["happy", "joy"]
        assert data["user_id"] == "user_123"

    def test_from_dict(self):
        data = {
            "emotion": "excited",
            "intensity": 0.9,
            "timestamp": "2024-01-15T10:30:00",
            "keywords": ["excited"],
            "context": "Can't wait!",
            "user_id": "user_456",
            "agent_id": "agent_1",
        }
        
        record = EmotionalStateRecord.from_dict(data)
        
        assert record.emotion == "excited"
        assert record.intensity == 0.9
        assert record.user_id == "user_456"


class TestEmotionalSummary:
    def test_to_dict(self):
        summary = EmotionalSummary(
            user_id="user_123",
            period_start=datetime(2024, 1, 1, 0, 0, 0),
            period_end=datetime(2024, 1, 15, 23, 59, 59),
            emotion_counts={"happy": 10, "excited": 5},
            dominant_emotion="happy",
            average_intensity=0.75,
            summary_text="User was mostly happy",
        )
        
        data = summary.to_dict()
        
        assert data["user_id"] == "user_123"
        assert data["dominant_emotion"] == "happy"
        assert data["emotion_counts"]["happy"] == 10

    def test_from_dict(self):
        data = {
            "user_id": "user_789",
            "period_start": "2024-01-01T00:00:00",
            "period_end": "2024-01-31T23:59:59",
            "emotion_counts": {"sad": 3, "calm": 7},
            "dominant_emotion": "calm",
            "average_intensity": 0.5,
            "summary_text": "User was calm",
            "archived_at": "2024-02-01T12:00:00",
        }
        
        summary = EmotionalSummary.from_dict(data)
        
        assert summary.user_id == "user_789"
        assert summary.dominant_emotion == "calm"


class TestEmotionalHistoryRepository:
    @pytest.mark.asyncio
    async def test_store_emotional_state_success(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_redis.client.lpush = AsyncMock()
        mock_redis.client.llen = AsyncMock(return_value=5)
        
        repo = EmotionalHistoryRepository(mock_redis)
        
        result = await repo.store_emotional_state(
            user_id="user_123",
            emotion="happy",
            intensity=0.8,
            context="Feeling good!",
            keywords=["happy"],
            agent_id="system",
        )
        
        assert result is True
        mock_redis.client.lpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_emotional_state_no_redis(self):
        repo = EmotionalHistoryRepository(None)
        
        result = await repo.store_emotional_state(
            user_id="user_123",
            emotion="happy",
            intensity=0.8,
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_recent_emotions(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lrange = AsyncMock(return_value=[
            json.dumps({"emotion": "happy", "intensity": 0.8}),
            json.dumps({"emotion": "excited", "intensity": 0.9}),
        ])
        
        repo = EmotionalHistoryRepository(mock_redis)
        
        result = await repo.get_recent_emotions("user_123", limit=5)
        
        assert len(result) == 2
        assert result[0]["emotion"] == "happy"
        assert result[1]["emotion"] == "excited"

    @pytest.mark.asyncio
    async def test_get_recent_emotions_empty(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lrange = AsyncMock(return_value=[])
        
        repo = EmotionalHistoryRepository(mock_redis)
        
        result = await repo.get_recent_emotions("user_123")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_archive_emotions(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_redis.client.lpush = AsyncMock()
        mock_redis.client.llen = AsyncMock(return_value=1)
        
        repo = EmotionalHistoryRepository(mock_redis)
        
        summary_data = {"dominant_emotion": "happy", "emotion_counts": {"happy": 10}}
        
        result = await repo.archive_emotions("user_123", summary_data)
        
        assert result is True
        mock_redis.client.lpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_archived_summaries(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lrange = AsyncMock(return_value=[
            json.dumps({"dominant_emotion": "happy", "emotion_counts": {"happy": 5}}),
        ])
        
        repo = EmotionalHistoryRepository(mock_redis)
        
        result = await repo.get_archived_summaries("user_123")
        
        assert len(result) == 1
        assert result[0]["dominant_emotion"] == "happy"


class TestEmotionalHistoryService:
    @pytest.mark.asyncio
    async def test_detect_and_store_emotion_detects_emotion(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_redis.client.lpush = AsyncMock()
        mock_redis.client.llen = AsyncMock(return_value=1)
        
        service = EmotionalHistoryService(redis_client=mock_redis)
        
        result = await service.detect_and_store_emotion(
            user_id="user_123",
            message="I am so happy today!",
            agent_id="system",
        )
        
        assert result is not None
        assert result.emotion in ["happy", "excited"]
        mock_redis.client.lpush.assert_called()

    @pytest.mark.asyncio
    async def test_detect_and_store_emotion_no_emotion(self):
        mock_redis = MagicMock()
        service = EmotionalHistoryService(redis_client=mock_redis)
        
        result = await service.detect_and_store_emotion(
            user_id="user_123",
            message="Hello, how are you?",
            agent_id="system",
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_emotional_context_with_history(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lrange = AsyncMock(return_value=[
            json.dumps({"emotion": "happy", "intensity": 0.8}),
            json.dumps({"emotion": "happy", "intensity": 0.7}),
            json.dumps({"emotion": "sad", "intensity": 0.5}),
        ])
        
        service = EmotionalHistoryService(redis_client=mock_redis)
        
        result = await service.get_emotional_context("user_123")
        
        assert result["has_history"] is True
        assert result["current_emotion"] == "happy"
        assert result["context_length"] == 3
        assert result["emotion_counts"]["happy"] == 2
        assert result["emotion_counts"]["sad"] == 1

    @pytest.mark.asyncio
    async def test_get_emotional_context_empty(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lrange = AsyncMock(return_value=[])
        
        service = EmotionalHistoryService(redis_client=mock_redis)
        
        result = await service.get_emotional_context("user_123")
        
        assert result["has_history"] is False
        assert result["current_emotion"] is None
        assert result["recent_emotions"] == []

    @pytest.mark.asyncio
    async def test_get_emotional_context_no_redis(self):
        service = EmotionalHistoryService(redis_client=None)
        
        result = await service.get_emotional_context("user_123")
        
        assert result["has_history"] is False

    @pytest.mark.asyncio
    async def test_get_full_context_includes_archived(self):
        mock_redis = MagicMock()
        mock_client = AsyncMock()
        mock_redis.client = mock_client
        mock_client.lrange = AsyncMock(return_value=[
            json.dumps({"emotion": "happy", "intensity": 0.8}),
        ])
        
        service = EmotionalHistoryService(redis_client=mock_redis)
        
        result = await service.get_full_context("user_123")
        
        assert "archived_summaries" in result
        assert "total_archived" in result
