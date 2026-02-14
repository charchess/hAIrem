"""
Integration tests for TTS Pipeline (Story 14.4)
Tests local TTS service and streaming capabilities
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Robust path handling
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BRIDGE_SRC = os.path.join(PROJECT_ROOT, 'apps', 'h-bridge', 'src')

if BRIDGE_SRC not in sys.path:
    sys.path.insert(0, BRIDGE_SRC)

# Mock optional dependencies
if 'melo' not in sys.modules:
    sys.modules['melo'] = MagicMock()
    sys.modules['melo.api'] = MagicMock()

if 'pyttsx3' not in sys.modules:
    sys.modules['pyttsx3'] = MagicMock()

# Import the service
try:
    from handlers.tts import TTSService
except ImportError:
    from apps.h_bridge.src.handlers.tts import TTSService

class TestTTSPipeline:
    
    @pytest.mark.asyncio
    async def test_tts_initialization(self):
        """Test TTS service initialization."""
        mock_redis = AsyncMock()
        service = TTSService(mock_redis)
        
        # Test initialization with fallback (pyttsx3)
        with patch('handlers.tts.MELO_AVAILABLE', False):
            with patch('handlers.tts.PYTTSX3_AVAILABLE', True):
                result = await service.initialize()
                assert result == True
                assert service.engine_type == "pyttsx3"
                assert service.is_initialized == True
        
        # Cleanup
        await service.cleanup()
        print("✅ TTS initialization test passed")
    
    @pytest.mark.asyncio
    async def test_tts_request_processing(self):
        """Test processing of TTS requests."""
        mock_redis = AsyncMock()
        service = TTSService(mock_redis)
        service.loop = asyncio.new_event_loop() # Mock loop
        
        # Initialize
        await service.initialize(engine="pyttsx3")
        
        # Mock dependencies
        mock_engine = MagicMock()
        with patch('pyttsx3.init', return_value=mock_engine):
            with patch('builtins.open', MagicMock()):
                with patch('os.remove', MagicMock()):
                    with patch('base64.b64encode', return_value=b'test_audio'):
                        
                        # Process a request
                        service._dispatch_event = AsyncMock()
                        
                        # Use the private synchronous method for testing logic
                        service._process_tts_request("req_1", "Hello world", {}, mock_engine)
                        
                        # Verify engine calls
                        mock_engine.save_to_file.assert_called()
                        mock_engine.runAndWait.assert_called()
                        
                        # Verify event dispatch
                        assert service._dispatch_event.call_count >= 3 # Start, Chunk, End
        
        await service.cleanup()
        print("✅ TTS request processing test passed")
    
    @pytest.mark.asyncio
    async def test_streaming_logic(self):
        """Test streaming logic structure."""
        mock_redis = AsyncMock()
        service = TTSService(mock_redis)
        
        # Test queuing mechanism
        req_id = await service.speak("Test streaming")
        
        assert not service.request_queue.empty()
        item = service.request_queue.get()
        assert item[0] == req_id
        assert item[1] == "Test streaming"
        
        print("✅ Streaming logic test passed")

if __name__ == '__main__':
    sys.exit(pytest.main([__file__]))
