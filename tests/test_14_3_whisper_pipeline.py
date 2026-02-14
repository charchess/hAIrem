"""
Integration tests for Whisper Pipeline (Story 14.3)
Tests local Whisper service and frontend integration
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Robust path handling
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BRIDGE_SRC = os.path.join(PROJECT_ROOT, 'apps', 'h-bridge', 'src')

if BRIDGE_SRC not in sys.path:
    sys.path.insert(0, BRIDGE_SRC)

# Mock modules if they are missing
if 'faster_whisper' not in sys.modules:
    sys.modules['faster_whisper'] = MagicMock()

if 'torch' not in sys.modules:
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    sys.modules['torch'] = mock_torch

# Import the service using the path that matches source code expectations
try:
    from handlers.whisper import WhisperService
except ImportError:
    # Fallback for different environments
    from apps.h_bridge.src.handlers.whisper import WhisperService

class TestWhisperPipeline:
    
    @pytest.mark.asyncio
    async def test_whisper_service_initialization(self):
        """Test Whisper service initialization."""
        mock_redis = AsyncMock()
        
        service = WhisperService(mock_redis)
        
        # Test successful initialization with default parameters
        with patch('faster_whisper.WhisperModel') as mock_model_cls:
            mock_model_instance = MagicMock()
            mock_model_cls.return_value = mock_model_instance
            
            # Mock transcribe method
            mock_model_instance.transcribe.return_value = ([], {})
            
            result = await service.initialize()
            
            assert result == True
            assert service.is_initialized == True
            assert service.model is not None
            assert service.model_size == "base"
            assert service.is_processing == True
            
            # Cleanup
            await service.cleanup()
        
        print("✅ Whisper service initialization successful")
    
    @pytest.mark.asyncio
    async def test_audio_processing(self):
        """Test audio processing and transcription."""
        mock_redis = AsyncMock()
        service = WhisperService(mock_redis)
        service.loop = asyncio.new_event_loop() # Mock loop
        
        # Initialize service with mocks
        with patch('faster_whisper.WhisperModel') as mock_model_cls:
            mock_model_instance = MagicMock()
            mock_model_cls.return_value = mock_model_instance
            
            # Mock the transcription result (segments, info)
            mock_segments = [MagicMock(text="test transcription", avg_logprob=-0.5)]
            mock_info = MagicMock(language="en")
            
            # Mock BOTH the __init__ call and the manual call in initialize()
            mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
            
            # Don't start the thread for this test
            with patch('threading.Thread'):
                await service.initialize()
            
            # Reset mock to count only the test call
            mock_model_instance.transcribe.reset_mock()
            mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
            
            # Test audio chunk processing
            test_audio = np.zeros(16000, dtype=np.float32)
            
            # Mock FFmpeg subprocess
            with patch('subprocess.Popen') as mock_popen:
                mock_proc = MagicMock()
                mock_popen.return_value = mock_proc
                mock_proc.communicate.return_value = (test_audio.tobytes(), b"")
                mock_proc.returncode = 0
                
                # Test synchronous processing directly
                def side_effect(coro, loop):
                    # In newer python/pytest, we should just return a dummy task or handle the coro
                    return MagicMock()

                with patch('asyncio.run_coroutine_threadsafe', side_effect=side_effect) as mock_run_threadsafe:
                    # In test environment, manually set segments_list as a list
                    # This bypasses the generator issues during mocking
                    with patch('handlers.whisper.list', return_value=mock_segments):
                        service._process_audio_chunk_sync("test_session", b"fake_bytes")
                    
                    # Verify transcription was called
                    mock_model_instance.transcribe.assert_called()
                    
                    # Verify callbacks were scheduled
                    assert mock_run_threadsafe.call_count >= 2
            
            # Cleanup
            await service.cleanup()
        
        print("✅ Audio processing test passed")
    
    @pytest.mark.asyncio
    async def test_session_management(self):
        """Test session lifecycle management."""
        mock_redis = AsyncMock()
        service = WhisperService(mock_redis)
        
        # Test session start
        session_data = await service.start_session("test_session")
        
        assert session_data['status'] == 'started'
        assert session_data['session_id'] == 'test_session'
        assert 'test_session' in service.active_sessions
        
        # Test session end
        session_end_data = await service.end_session("test_session")
        
        assert session_end_data['status'] == 'ended'
        assert 'duration' in session_end_data
        assert 'test_session' not in service.active_sessions
        
        print("✅ Session management test passed")

    @pytest.mark.asyncio
    async def test_service_metrics(self):
        """Test metrics collection."""
        mock_redis = AsyncMock()
        service = WhisperService(mock_redis)
        
        metrics = service.get_metrics()
        assert 'transcriptions_processed' in metrics
        assert 'average_latency' in metrics
        
        print("✅ Metrics test passed")

if __name__ == '__main__':
    # Allow running directly
    sys.exit(pytest.main([__file__]))
