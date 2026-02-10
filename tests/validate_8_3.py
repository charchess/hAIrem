import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add apps/h-core to path
sys.path.append(str(Path(__file__).parent.parent / "apps" / "h-core"))

from src.infrastructure.llm import LlmClient
from src.infrastructure.surrealdb import SurrealDbClient
from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig

async def validate_rag_infrastructure():
    print("--- Validating RAG Infrastructure (Story 8.3) ---")
    
    # 1. Test Embedding Generation
    print("\n1. Testing Embedding Generation...")
    llm = LlmClient()
    # Mock aembedding to avoid API calls if not configured
    with patch("src.infrastructure.llm.aembedding", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = MagicMock(data=[{"embedding": [0.1] * 1536}])
        emb = await llm.get_embedding("Test text")
        assert len(emb) == 1536, f"Embedding length mismatch: {len(emb)}"
        print("✅ Embedding generation verified (mocked).")

    # 2. Test Semantic Search Query
    print("\n2. Testing Semantic Search Query...")
    surreal = SurrealDbClient()
    with patch.object(SurrealDbClient, 'connect', new_callable=AsyncMock):
        surreal.client = MagicMock()
        surreal.client.query = AsyncMock(return_value=[{"id": "msg:1", "payload": {"content": "Found!"}}])
        
        results = await surreal.semantic_search([0.1]*1536)
        assert len(results) > 0, "No results returned from search"
        print("✅ Semantic search query verified (mocked).")

    # 3. Test Agent Tool Registration
    print("\n3. Testing recall_memory Tool Registration...")
    config = AgentConfig(name="TestAgent", role="Tester", description="Test", version="1.0", capabilities=[], prompt="Test")
    agent = BaseAgent(config=config, redis_client=MagicMock(), llm_client=llm, surreal_client=surreal)
    
    assert "recall_memory" in agent.tools, "recall_memory tool not registered on agent"
    print("✅ recall_memory tool registration verified.")

    print("\n--- Story 8.3 Validation SUCCESS ---")

if __name__ == "__main__":
    asyncio.run(validate_rag_infrastructure())
