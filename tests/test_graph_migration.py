import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Add apps/h-core to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', 'h-core')))

from src.infrastructure.surrealdb import SurrealDbClient
from scripts.migrate_memories_v2_to_v3 import migrate

@pytest.fixture
def mock_surreal():
    # Use the local path if needed
    with patch("src.infrastructure.surrealdb.Surreal", create=True) as mock, \
         patch("src.infrastructure.surrealdb.SURREAL_AVAILABLE", True):
        yield mock

@pytest.mark.asyncio
async def test_migration_flow(mock_surreal):
    """Verifies that the migration script calls insert_graph_memory for each old memory."""
    client_mock = mock_surreal.return_value
    
    # Mock 'query' result for old memories
    mock_old_memories = [
        {"fact": "User likes blue", "subject": "user", "agent": "system", "confidence": 1.0, "embedding": [0.1]*384},
        {"fact": "Renarde is an agent", "subject": "renarde", "agent": "system", "confidence": 1.0, "embedding": [0.2]*384}
    ]
    
    # SurrealDB library response format
    client_mock.query = AsyncMock(return_value=[{"result": mock_old_memories, "status": "OK"}])
    client_mock.signin = AsyncMock()
    client_mock.use = AsyncMock()
    
    # Patch SurrealDbClient to capture calls to insert_graph_memory
    with patch("src.infrastructure.surrealdb.SurrealDbClient.insert_graph_memory", new_callable=AsyncMock) as mock_insert:
        await migrate()
        
        # Verify insert_graph_memory was called twice
        assert mock_insert.call_count == 2
        
        # Check first call data
        args, _ = mock_insert.call_args_list[0]
        assert args[0]["fact"] == "User likes blue"
        assert args[0]["subject"] == "user"
