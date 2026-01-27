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
    from src.main import main, sleep_cycle_loop

@pytest.mark.asyncio
async def test_sleep_cycle_loop_trigger():
    mock_consolidator = AsyncMock()
    
    # Set interval to 0.1 for fast testing
    with patch.dict(os.environ, {"SLEEP_CYCLE_INTERVAL": "0.1"}), \
         patch("src.main.consolidator", mock_consolidator):
        
        # Start the loop in a background task
        task = asyncio.create_task(sleep_cycle_loop())
        
        # Wait for more than 0.1 second to ensure at least one cycle
        await asyncio.sleep(0.5)
        
        # Stop the loop
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # Verify consolidation was called
    assert mock_consolidator.consolidate.called
    assert mock_consolidator.apply_decay.called

@pytest.mark.asyncio
async def test_startup_initializes_consolidator():
    # Reset consolidator
    import src.main
    src.main.consolidator = None
    
    # We need to mock infrastructure and other startup calls
    with patch("src.main.redis_client.connect", new_callable=AsyncMock), \
         patch("src.main.surreal_client.connect", new_callable=AsyncMock), \
         patch("src.main.RedisLogHandler"), \
         patch("src.main.plugin_loader.start", new_callable=AsyncMock), \
         patch("asyncio.gather", new_callable=AsyncMock):
        
        # main() will gather loops, we just want to see if consolidator is set before that
        try:
            await asyncio.wait_for(main(), timeout=0.1)
        except (asyncio.TimeoutError, Exception):
            pass
        
        assert src.main.consolidator is not None