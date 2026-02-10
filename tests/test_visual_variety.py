import asyncio
import os
import sys
import tempfile
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

# Add apps/h-core to sys.path
sys.path.append(str(Path(__file__).parent.parent / "apps" / "h-core"))

from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig

async def test_visual_variety_logic():
    print("🚀 Testing Visual Variety Logic...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_redis = MagicMock()
        mock_llm = MagicMock()
        mock_imagen = MagicMock()
        mock_imagen.generate_image = AsyncMock(return_value="job_123")
        
        config = AgentConfig(name="test_agent\