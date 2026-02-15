import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import os

# Mock infrastructure before importing main
with patch("src.infrastructure.redis.RedisClient"), \
     patch("src.infrastructure.surrealdb.SurrealDbClient"), \
     patch("src.infrastructure.llm.LlmClient"), \
     patch("src.infrastructure.plugin_loader.PluginLoader"), \
     patch("src.domain.memory.MemoryConsolidator"):
    from src.main import HaremOrchestrator

@pytest.mark.asyncio
async def test_sleep_cycle_worker_exists():
    """Test that sleep cycle worker method exists and is callable."""
    # Create orchestrator with proper mocking
    with patch("src.main.RedisClient") as mock_redis_class, \
         patch("src.main.SurrealDbClient") as mock_surreal_class, \
         patch("src.main.LlmClient") as mock_llm_class:
        
        mock_redis_class.return_value = AsyncMock()
        mock_surreal_class.return_value = AsyncMock()
        mock_llm_class.return_value = AsyncMock()
        
        orchestrator = HaremOrchestrator()
        
        # Verify sleep_cycle_worker method exists
        assert hasattr(orchestrator, 'sleep_cycle_worker')
        assert callable(orchestrator.sleep_cycle_worker)

@pytest.mark.asyncio
async def test_orchestrator_has_consolidator():
    """Test that orchestrator has consolidator attribute."""
    # Create orchestrator with proper mocking
    with patch("src.main.RedisClient") as mock_redis_class, \
         patch("src.main.SurrealDbClient") as mock_surreal_class, \
         patch("src.main.LlmClient") as mock_llm_class:
        
        mock_redis_class.return_value = AsyncMock()
        mock_surreal_class.return_value = AsyncMock()
        mock_llm_class.return_value = AsyncMock()
        
        # Create orchestrator
        orchestrator = HaremOrchestrator()
        
        # Verify consolidator attribute exists
        assert hasattr(orchestrator, 'consolidator')