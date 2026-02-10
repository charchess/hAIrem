import asyncio
import sys
import os

# Add apps/h-core to path
sys.path.append(os.path.join(os.getcwd(), "apps", "h-core"))

from unittest.mock import AsyncMock, MagicMock
from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig
from src.services.visual.service import VisualImaginationService
from src.services.visual.vault import VaultService

async def test_agent_tool_vault():
    mock_redis = MagicMock()
    mock_redis.publish = AsyncMock()
    mock_llm = MagicMock()
    mock_llm.get_embedding = AsyncMock(return_value=[0.1]*768)
    
    mock_db = MagicMock()
    mock_db._call = AsyncMock()
    
    config = AgentConfig(name="lisa", role="companion")
    
    # We need a real-ish VaultService for it to work
    vault = VaultService(mock_db)
    
    # Mocking vs.vault
    vs = MagicMock()
    vs.vault = vault
    
    agent = BaseAgent(config, mock_redis, mock_llm, surreal_client=mock_db, visual_service=vs)
    
    # Check tool registration
    if "save_to_vault" not in agent.tools:
        print("FAIL: save_to_vault tool NOT registered")
        return

    # Mock finding latest asset in SurrealDB
    # BaseAgent.save_to_vault does: res = await self.surreal._call("query", query)
    mock_db._call.return_value = [{"result": [{"id": "visual_asset:test_id"}]}]
    
    # Test execution
    result = await agent.save_to_vault(name="cyberpunk_ninja", category="garment")
    print(f"Result: {result}")
    
    if "Success" in result:
        print("PASS: save_to_vault tool executed successfully")
    else:
        print(f"FAIL: save_to_vault tool returned error: {result}")
    
    # Verify DB call
    # 1. Latest asset query
    # 2. Vault save query
    assert mock_db._call.call_count >= 2

if __name__ == "__main__":
    asyncio.run(test_agent_tool_vault())
