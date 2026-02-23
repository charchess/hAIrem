import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.features.home.memory.episode import Episode
from src.features.home.memory.episode_service import EpisodeService


@pytest.fixture
def mock_surreal():
    s = AsyncMock()
    s.open_episode.return_value = "episode:sess_abc"
    s.close_episode.return_value = True
    s.get_episode.return_value = {
        "id": "episode:sess_abc",
        "session_id": "sess_abc",
        "agent_id": "renarde",
        "user_id": "user_1",
        "ended_at": None,
        "summary": None,
        "emotion_arc": [],
    }
    s.get_episode_facts.return_value = [
        {"id": "fact:1", "content": "User loves coffee"},
        {"id": "fact:2", "content": "User works as a developer"},
    ]
    s.get_recent_episodes.return_value = []
    return s


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.get_completion.return_value = "This episode covered the user's coffee preference and work background."
    return llm


@pytest.fixture
def service(mock_surreal, mock_llm):
    return EpisodeService(mock_surreal, mock_llm)


class TestEpisode:
    def test_is_open_when_no_ended_at(self):
        ep = Episode(episode_id="ep:1", session_id="s1", agent_id="agent1")
        assert ep.is_open() is True

    def test_is_closed_when_ended_at_set(self):
        ep = Episode(episode_id="ep:1", session_id="s1", agent_id="agent1", ended_at=datetime.utcnow())
        assert ep.is_open() is False

    def test_to_dict_keys(self):
        ep = Episode(episode_id="ep:1", session_id="s1", agent_id="agent1")
        d = ep.to_dict()
        assert "episode_id" in d
        assert "session_id" in d
        assert "agent_id" in d
        assert "started_at" in d
        assert "ended_at" in d
        assert d["ended_at"] is None


class TestEpisodeServiceOpen:
    @pytest.mark.asyncio
    async def test_open_episode_creates_record(self, service, mock_surreal):
        ep = await service.open_episode("sess_abc", "renarde", "user_1")
        mock_surreal.open_episode.assert_called_once_with("sess_abc", "renarde", "user_1")
        assert ep.session_id == "sess_abc"
        assert ep.agent_id == "renarde"
        assert ep.user_id == "user_1"
        assert ep.is_open()

    @pytest.mark.asyncio
    async def test_open_episode_without_user(self, service, mock_surreal):
        mock_surreal.open_episode.return_value = "episode:no_user"
        ep = await service.open_episode("sess_xyz", "renarde")
        assert ep.user_id is None


class TestEpisodeServiceClose:
    @pytest.mark.asyncio
    async def test_close_episode_generates_summary(self, service, mock_surreal, mock_llm):
        mock_surreal.get_episode.return_value = {
            "id": "episode:sess_abc",
            "session_id": "sess_abc",
            "agent_id": "renarde",
            "user_id": "user_1",
            "ended_at": "2026-02-23T12:00:00",
            "summary": None,
            "emotion_arc": [],
        }
        ep = await service.close_episode("sess_abc", [{"emotion": "joy", "intensity": 0.8}])
        assert ep.summary is not None
        assert len(ep.summary) > 0
        mock_surreal.close_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_episode_no_facts_returns_empty_summary(self, service, mock_surreal):
        mock_surreal.get_episode_facts.return_value = []
        mock_surreal.get_episode.return_value = {
            "id": "episode:sess_empty",
            "session_id": "sess_empty",
            "agent_id": "renarde",
            "user_id": None,
            "ended_at": "2026-02-23T12:00:00",
            "summary": None,
            "emotion_arc": [],
        }
        ep = await service.close_episode("sess_empty")
        assert ep.summary == ""

    @pytest.mark.asyncio
    async def test_close_episode_stores_emotion_arc(self, service, mock_surreal):
        arc = [{"emotion": "sadness", "intensity": 0.5}]
        mock_surreal.get_episode.return_value = {
            "id": "episode:sess_abc",
            "session_id": "sess_abc",
            "agent_id": "renarde",
            "user_id": None,
            "ended_at": "2026-02-23T12:00:00",
            "summary": None,
            "emotion_arc": arc,
        }
        ep = await service.close_episode("sess_abc", arc)
        assert ep.emotion_arc == arc


class TestEpisodeServiceGetContext:
    @pytest.mark.asyncio
    async def test_get_episode_context_returns_dict(self, service, mock_surreal):
        ctx = await service.get_episode_context("sess_abc")
        assert ctx["session_id"] == "sess_abc"
        assert "facts" in ctx
        assert isinstance(ctx["facts"], list)

    @pytest.mark.asyncio
    async def test_get_episode_context_missing_session(self, service, mock_surreal):
        mock_surreal.get_episode.return_value = None
        ctx = await service.get_episode_context("nonexistent")
        assert ctx == {}


class TestEpisodeServiceTemporalContext:
    @pytest.mark.asyncio
    async def test_get_temporal_context_empty(self, service, mock_surreal):
        episodes = await service.get_temporal_context("renarde")
        assert episodes == []

    @pytest.mark.asyncio
    async def test_get_temporal_context_filters_old_episodes(self, service, mock_surreal):
        mock_surreal.get_recent_episodes.return_value = [
            {
                "id": "episode:old",
                "session_id": "sess_old",
                "agent_id": "renarde",
                "user_id": None,
                "started_at": "2020-01-01T00:00:00",
                "ended_at": "2020-01-01T01:00:00",
                "summary": "old episode",
                "emotion_arc": [],
            }
        ]
        episodes = await service.get_temporal_context("renarde", since_days=7)
        assert episodes == []

    @pytest.mark.asyncio
    async def test_get_temporal_context_includes_recent(self, service, mock_surreal):
        from datetime import timedelta

        now = datetime.utcnow()
        recent = (now - timedelta(days=1)).isoformat()
        mock_surreal.get_recent_episodes.return_value = [
            {
                "id": "episode:recent",
                "session_id": "sess_recent",
                "agent_id": "renarde",
                "user_id": "user_1",
                "started_at": recent,
                "ended_at": None,
                "summary": "recent episode",
                "emotion_arc": [{"emotion": "joy"}],
            }
        ]
        episodes = await service.get_temporal_context("renarde", since_days=7)
        assert len(episodes) == 1
        assert episodes[0].session_id == "sess_recent"
