"""
Test Suite for Story 3.2 - WebSocket Bridge
Tests WebSocket implementation using FastAPI TestClient
"""

import pytest
import asyncio
import json
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Add apps/h-bridge to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', 'h-bridge')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', 'h-bridge', 'src')))

# Mock heavy dependencies before importing app
sys.modules['torch'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['pyttsx3'] = MagicMock()
sys.modules['melo'] = MagicMock()
sys.modules['melo.api'] = MagicMock()

# Mock StaticFiles to avoid directory not found error for /app/agents
class MockStaticFiles:
    def __init__(self, directory=None, **kwargs):
        pass
    def mount(self, *args, **kwargs):
        pass

sys.modules['fastapi.staticfiles'] = MagicMock(StaticFiles=MockStaticFiles)

try:
    from fastapi.testclient import TestClient
    try:
        from src.main import app
    except ImportError:
        from main import app
    
    WEBSOCKET_MODULES_AVAILABLE = True
except ImportError as e:
    WEBSOCKET_MODULES_AVAILABLE = False
    print(f"WebSocket modules not found: {e}")


class TestStory3_2WebSocketBridge:
    """
    Test Story 3.2 - WebSocket Bridge using TestClient
    """
    
    def test_websocket_endpoint_exists(self):
        """Test WebSocket endpoint accessibility"""
        if not WEBSOCKET_MODULES_AVAILABLE:
            pytest.fail("WebSocket modules not available")
            
        client = TestClient(app)
        
        # Test connection
        with patch('src.infrastructure.redis.RedisClient.listen_stream') as mock_listen:
            # We mock the listen_stream to avoid infinite loop waiting for redis
            mock_listen.return_value = None
            
            with client.websocket_connect("/ws") as websocket:
                # Connection successful if we are here
                pass

    def test_websocket_message_handling(self):
        """Test WebSocket message handling"""
        if not WEBSOCKET_MODULES_AVAILABLE:
            pytest.skip("WebSocket modules not available")
            
        client = TestClient(app)
        
        with patch('src.infrastructure.redis.RedisClient.listen_stream', new_callable=AsyncMock) as mock_listen:
            with patch('src.infrastructure.redis.RedisClient.publish_event', new_callable=AsyncMock) as mock_publish:
                with client.websocket_connect("/ws") as websocket:
                    # Send message
                    test_message = {
                        "type": "user_message",
                        "sender": {"agent_id": "user", "role": "user"},
                        "recipient": {"target": "all"},
                        "payload": {"content": "hello"}
                    }
                    websocket.send_json(test_message)

if __name__ == "__main__":
    pytest.main([__file__])
