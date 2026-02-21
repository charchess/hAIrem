from unittest.mock import AsyncMock, MagicMock
import pytest
from src.services.relationship_bootstrapper import RelationshipBootstrapper
from src.infrastructure.surrealdb import SurrealDbClient


@pytest.fixture
def mock_surreal():
    mock = MagicMock(spec=SurrealDbClient)
    mock._call = AsyncMock()

    # Return empty list for SELECT queries to simulate no existing relationships
    async def side_effect(method, query, params=None):
        if method == "query" and "SELECT" in query:
            return []
        else:
            return None  # For RELATE queries

    mock._call.side_effect = side_effect
    return mock


@pytest.mark.asyncio
async def test_bootstrap_relationships(mock_surreal: SurrealDbClient):
    bootstrapper = RelationshipBootstrapper(mock_surreal)
    agents = [{"name": "agent1", "role": "expert"}, {"name": "agent2", "role": "expert"}]
    result = await bootstrapper.bootstrap_relationships(agents)
    assert result["KNOWS"] == 2  # Bidirectional
    assert result["TRUSTS"] == 2
    # Verify queries were called (4 SELECT + 4 RELATE + 2 INSERT)
    assert mock_surreal._call.call_count >= 8
