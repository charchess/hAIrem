import pytest
from unittest.mock import AsyncMock, MagicMock
from src.features.home.per_user_memory import UserMemoryContext, UserMemoryService
from src.domain.memory import MemoryConsolidator


class TestUserMemoryContext:
    """Tests for UserMemoryContext class."""

    def test_set_user_basic(self):
        """Test basic user setting."""
        context = UserMemoryContext()
        
        context.set_user("user_123", "Alice")
        
        assert context.current_user_id == "user_123"
        assert context.current_user_name == "Alice"

    def test_set_user_without_name(self):
        """Test setting user without name."""
        context = UserMemoryContext()
        
        context.set_user("user_456")
        
        assert context.current_user_id == "user_456"
        assert context.current_user_name is None

    def test_set_user_with_session(self):
        """Test setting user with session_id."""
        context = UserMemoryContext()
        
        context.set_user("user_123", "Alice", session_id="session_abc")
        
        assert context.current_user_id == "user_123"
        assert context.session_id == "session_abc"

    def test_set_user_switch_records_history(self):
        """Test that switching users records history."""
        context = UserMemoryContext()
        
        context.set_user("user_1", "Alice")
        context.set_user("user_2", "Bob")
        
        assert len(context.user_history) == 1
        assert context.user_history[0]["from_user"] == "user_1"
        assert context.user_history[0]["to_user"] == "user_2"
        assert context.user_history[0]["action"] == "switch"

    def test_set_user_same_user_no_history(self):
        """Test that setting the same user doesn't add to history."""
        context = UserMemoryContext()
        
        context.set_user("user_1", "Alice")
        context.set_user("user_1", "Alice2")
        
        assert len(context.user_history) == 0

    def test_get_user(self):
        """Test get_user returns correct tuple."""
        context = UserMemoryContext()
        
        context.set_user("user_123", "Alice")
        
        user_id, user_name = context.get_user()
        
        assert user_id == "user_123"
        assert user_name == "Alice"

    def test_get_user_no_user(self):
        """Test get_user when no user is set."""
        context = UserMemoryContext()
        
        user_id, user_name = context.get_user()
        
        assert user_id is None
        assert user_name is None

    def test_clear(self):
        """Test clear resets all context."""
        context = UserMemoryContext()
        
        context.set_user("user_123", "Alice", session_id="session_abc")
        context.clear()
        
        assert context.current_user_id is None
        assert context.current_user_name is None
        assert context.session_id is None

    def test_has_user(self):
        """Test has_user returns correct status."""
        context = UserMemoryContext()
        
        assert context.has_user() is False
        
        context.set_user("user_123", "Alice")
        
        assert context.has_user() is True
        
        context.clear()
        
        assert context.has_user() is False


class TestUserMemoryService:
    """Tests for UserMemoryService class."""

    @pytest.mark.asyncio
    async def test_get_user_memories_success(self):
        """Test get_user_memories calls semantic_search_user correctly."""
        mock_surreal = AsyncMock()
        mock_surreal.semantic_search_user.return_value = [
            {"content": "User likes coffee", "user_id": "user_123"}
        ]
        
        service = UserMemoryService(mock_surreal)
        embedding = [0.1, 0.2, 0.3]
        results = await service.get_user_memories("user_123", embedding, limit=5)
        
        mock_surreal.semantic_search_user.assert_called_once_with(embedding, "user_123", 5)
        assert len(results) == 1
        assert results[0]["content"] == "User likes coffee"

    @pytest.mark.asyncio
    async def test_get_user_memories_default_limit(self):
        """Test get_user_memories uses default limit."""
        mock_surreal = AsyncMock()
        mock_surreal.semantic_search_user.return_value = []
        
        service = UserMemoryService(mock_surreal)
        embedding = [0.1, 0.2]
        await service.get_user_memories("user_123", embedding)
        
        mock_surreal.semantic_search_user.assert_called_once_with(embedding, "user_123", 3)

    @pytest.mark.asyncio
    async def test_get_user_memories_no_surreal(self):
        """Test get_user_memories returns empty list when no surreal client."""
        service = UserMemoryService(None)
        
        results = await service.get_user_memories("user_123", [0.1, 0.2])
        
        assert results == []

    @pytest.mark.asyncio
    async def test_get_user_memories_error_handling(self):
        """Test get_user_memories handles errors gracefully."""
        mock_surreal = AsyncMock()
        mock_surreal.semantic_search_user.side_effect = Exception("DB error")
        
        service = UserMemoryService(mock_surreal)
        
        results = await service.get_user_memories("user_123", [0.1, 0.2])
        
        assert results == []

    @pytest.mark.asyncio
    async def test_store_memory_with_user(self):
        """Test store_memory_with_user associates user_id."""
        mock_surreal = AsyncMock()
        
        service = UserMemoryService(mock_surreal)
        
        fact_data = {"content": "User likes tea"}
        result = await service.store_memory_with_user(fact_data, "user_123", "Alice")
        
        assert result is True
        mock_surreal.insert_graph_memory.assert_called_once()
        call_args = mock_surreal.insert_graph_memory.call_args[0][0]
        assert call_args["user_id"] == "user_123"
        assert call_args["user_name"] == "Alice"

    @pytest.mark.asyncio
    async def test_store_memory_without_name(self):
        """Test store_memory_with_user works without user_name."""
        mock_surreal = AsyncMock()
        
        service = UserMemoryService(mock_surreal)
        
        fact_data = {"content": "User likes tea"}
        result = await service.store_memory_with_user(fact_data, "user_123")
        
        assert result is True
        call_args = mock_surreal.insert_graph_memory.call_args[0][0]
        assert call_args["user_id"] == "user_123"
        assert "user_name" not in call_args

    @pytest.mark.asyncio
    async def test_store_memory_no_surreal(self):
        """Test store_memory_with_user returns False without surreal client."""
        service = UserMemoryService(None)
        
        result = await service.store_memory_with_user({"content": "test"}, "user_123")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_universal_memories(self):
        """Test get_universal_memories calls semantic_search_universal."""
        mock_surreal = AsyncMock()
        mock_surreal.semantic_search_universal.return_value = [
            {"content": "System fact", "user_id": None}
        ]
        
        service = UserMemoryService(mock_surreal)
        embedding = [0.1, 0.2]
        results = await service.get_universal_memories(embedding, limit=3)
        
        mock_surreal.semantic_search_universal.assert_called_once_with(embedding, 3)
        assert len(results) == 1


class TestMemoryConsolidatorUserId:
    """Tests for MemoryConsolidator user_id association."""

    @pytest.mark.asyncio
    async def test_consolidate_associates_user_id(self):
        """Test that consolidate associates user_id with extracted facts."""
        mock_surreal = AsyncMock()
        mock_llm = AsyncMock()
        mock_redis = AsyncMock()
        
        mock_surreal.get_unprocessed_messages.return_value = [
            {
                "id": "messages:uuid1",
                "sender": {"agent_id": "user"},
                "payload": {"content": "I love green tea", "user_id": "user_abc"}
            }
        ]
        
        mock_llm.get_completion.return_value = '[{"fact": "User likes green tea", "subject": "user", "confidence": 0.9}]'
        mock_llm.get_embedding.return_value = [0.1, 0.2]
        mock_surreal.semantic_search.return_value = []
        
        consolidator = MemoryConsolidator(mock_surreal, mock_llm, mock_redis)
        facts_count = await consolidator.consolidate()
        
        assert facts_count == 1
        call_args = mock_surreal.insert_graph_memory.call_args[0][0]
        assert call_args["user_id"] == "user_abc"

    @pytest.mark.asyncio
    async def test_consolidate_no_user_id_when_missing(self):
        """Test consolidate works when user_id is not in payload."""
        mock_surreal = AsyncMock()
        mock_llm = AsyncMock()
        mock_redis = AsyncMock()
        
        mock_surreal.get_unprocessed_messages.return_value = [
            {
                "id": "messages:uuid1",
                "sender": {"agent_id": "user"},
                "payload": {"content": "I love green tea"}
            }
        ]
        
        mock_llm.get_completion.return_value = '[{"fact": "User likes green tea", "subject": "user", "confidence": 0.9}]'
        mock_llm.get_embedding.return_value = [0.1, 0.2]
        mock_surreal.semantic_search.return_value = []
        
        consolidator = MemoryConsolidator(mock_surreal, mock_llm, mock_redis)
        facts_count = await consolidator.consolidate()
        
        assert facts_count == 1
        call_args = mock_surreal.insert_graph_memory.call_args[0][0]
        assert "user_id" not in call_args

    @pytest.mark.asyncio
    async def test_consolidate_uses_primary_user_id(self):
        """Test consolidate uses first user_id when multiple users in batch."""
        mock_surreal = AsyncMock()
        mock_llm = AsyncMock()
        mock_redis = AsyncMock()
        
        mock_surreal.get_unprocessed_messages.return_value = [
            {
                "id": "messages:uuid1",
                "sender": {"agent_id": "user"},
                "payload": {"content": "Message 1", "user_id": "user_first"}
            },
            {
                "id": "messages:uuid2",
                "sender": {"agent_id": "user"},
                "payload": {"content": "Message 2", "user_id": "user_second"}
            }
        ]
        
        mock_llm.get_completion.return_value = '[{"fact": "Fact 1", "subject": "user", "confidence": 0.9}]'
        mock_llm.get_embedding.return_value = [0.1, 0.2]
        mock_surreal.semantic_search.return_value = []
        
        consolidator = MemoryConsolidator(mock_surreal, mock_llm, mock_redis)
        facts_count = await consolidator.consolidate()
        
        assert facts_count == 1
        call_args = mock_surreal.insert_graph_memory.call_args[0][0]
        assert call_args["user_id"] == "user_first"
