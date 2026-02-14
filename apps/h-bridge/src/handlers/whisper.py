"""
Whisper Service for hAIrem Audio Processing Pipeline
Implements local speech-to-text transcription using faster-whisper
"""

import asyncio
import logging
import numpy as np
import torch
import time
import json
from typing import Dict, Any, Optional, List
import threading
import queue  # Import standard queue

try:
    import faster_whisper
except ImportError as e:
    logging.error(f"faster_whisper not available: {e}")
    raise ImportError("faster-whisper is required for Whisper pipeline")

from models.hlink import HLinkMessage, MessageType, Payload, Sender, Recipient
from infrastructure.redis import RedisClient

logger = logging.getLogger(__name__)


class WhisperService:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.model = None
        self.model_size = "base"  # Can be "tiny", "base", "small", "medium", "large"
        self.device = "auto"  # Will auto-detect GPU/CPU
        self.is_initialized = False
        self.transcription_queue = queue.Queue()  # Use thread-safe queue
        self.active_sessions = {}  # Track active transcription sessions
        self.is_processing = False
        self.processing_thread = None
        self.loop = None  # Reference to the main event loop
        
        # Performance monitoring
        self.metrics = {
            'transcriptions_processed': 0,
            'total_audio_duration': 0.0,
            'average_latency': 0.0,
            'memory_usage': 0.0,
            'gpu_usage': False
        }
    
    async def initialize(self, model_size="base", device="auto"):
        """Initialize Whisper model and processing pipeline."""
        try:
            if self.is_initialized:
                logger.info("Whisper service already initialized")
                return True
            
            # Device selection
            if device == "auto":
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                self.device = device
            
            logger.info(f"Initializing Whisper with model_size={model_size}, device={self.device}")
            
            # Capture the current event loop for thread-safe callbacks
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning("No running event loop found during initialization")
            
            # Load Whisper model
            start_time = time.time()
            self.model = faster_whisper.WhisperModel(
                model_size_or_path=model_size,
                device=self.device,
                compute_type="float32"
            )
            
            # Warm up the model
            # Test with a short audio snippet
            test_audio = np.zeros(16000, dtype=np.float32)
            _ = self.model.transcribe(test_audio, language="fr", task="transcribe")
            
            load_time = time.time() - start_time
            logger.info(f"Whisper model loaded in {load_time:.2f}s")
            
            self.is_initialized = True
            self.model_size = model_size
            
            # Start processing thread
            self.is_processing = True
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True
            )
            self.processing_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Whisper initialization failed: {e}")
            return False
    
    def _processing_loop(self):
        """Background processing loop for transcription requests (runs in thread)."""
        logger.info("Starting Whisper processing loop")
        
        while self.is_processing:
            try:
                # Get transcription request from queue (blocking with timeout)
                try:
                    item = self.transcription_queue.get(timeout=1.0)
                    session_id, audio_data = item
                    
                    # Process synchronously in this thread
                    self._process_audio_chunk_sync(session_id, audio_data)
                    
                    self.transcription_queue.task_done()
                    
                except queue.Empty:
                    continue  # Timeout, check is_processing again
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.1)
    
    async def _send_to_llm(self, transcription_data: Dict[str, Any]):
        """Send transcription to LLM conversation pipeline."""
        try:
            message = HLinkMessage(
                type=MessageType.USER_MESSAGE,
                sender=Sender(agent_id="whisper_pipeline", role="transcriber"),
                recipient=Recipient(target="llm_router"),
                payload=Payload(
                    content=transcription_data['text'],
                    format="text",
                    source="whisper_transcription",
                    confidence=transcription_data['confidence'],
                    language=transcription_data['language'],
                    session_id=transcription_data['session_id']
                )
            )
            
            await self.redis_client.publish_event("conversation_stream", json.loads(message.model_dump_json()))
            
        except Exception as e:
            logger.error(f"Failed to send to LLM: {e}")

    async def _send_frontend_update(self, transcription_data: Dict[str, Any]):
        """Send transcription update to frontend via Redis Stream."""
        try:
            message = HLinkMessage(
                type=MessageType.TRANSCRIPTION_UPDATE,
                sender=Sender(agent_id="whisper_pipeline", role="transcriber"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(
                    content="Transcription available",
                    text=transcription_data['text'],
                    confidence=transcription_data['confidence'],
                    session_id=transcription_data['session_id']
                )
            )
            
            # STORY 14.3 FIX: Actually publish to system_stream so Bridge relays it to WS
            # Ensure serialization of datetime/UUID
            await self.redis_client.publish_event("system_stream", json.loads(message.model_dump_json()))
            logger.info(f"Transcription published to system_stream: {transcription_data['text'][:30]}...")
            
        except Exception as e:
            logger.error(f"Failed to send frontend update: {e}")

    def _process_audio_chunk_sync(self, session_id: str, audio_bytes: bytes):
        """Process a single audio chunk synchronously with FFmpeg decoding."""
        try:
            start_time = time.time()
            
            # STORY 14.3 FIX: Decode WebM/Opus/MP3 to PCM 16kHz using FFmpeg
            import subprocess
            
            process = subprocess.Popen(
                ['ffmpeg', '-i', 'pipe:0', '-f', 'f32le', '-acodec', 'pcm_f32le', '-ar', '16000', '-ac', '1', 'pipe:1'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            out, err = process.communicate(input=audio_bytes)
            
            if process.returncode != 0:
                logger.error(f"FFmpeg decoding failed: {err.decode()}")
                return

            audio_data = np.frombuffer(out, dtype=np.float32)
            
            # Transcribe using Whisper (blocking call)
            result = self.model.transcribe(
                audio_data,
                language="fr",
                task="transcribe",
                vad_filter=True
            )
            
            segments, info = result
            segments_list = list(segments)
            full_text = " ".join([segment.text for segment in segments_list])
            
            if not full_text.strip():
                return
                
            # Format result
            transcription_data = {
                'session_id': session_id,
                'text': full_text,
                'language': info.language,
                'confidence': np.exp(sum(s.avg_logprob for s in segments_list) / len(segments_list)) if segments_list else 0.0,
                'processing_time': time.time() - start_time,
                'audio_length': len(audio_data) / 16000,
                'model_size': self.model_size,
                'device': self.device
            }
            
            # Update metrics
            self.metrics['transcriptions_processed'] += 1
            self.metrics['total_audio_duration'] += len(audio_data) / 16000
            self.metrics['average_latency'] = (self.metrics['average_latency'] + transcription_data['processing_time']) / 2
            
            # Schedule async callbacks on the main event loop
            if self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(self._send_to_llm(transcription_data), self.loop)
                asyncio.run_coroutine_threadsafe(self._send_frontend_update(transcription_data), self.loop)
            
            # Update session tracking
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['chunks_processed'] += 1
                self.active_sessions[session_id]['total_duration'] += len(audio_data) / 16000
            
            logger.info(f"Processed transcription for session {session_id}: {full_text[:50]}...")
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            if self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(self._send_error_update(session_id, str(e)), self.loop)
    
    async def _send_error_update(self, session_id: str, error: str):
        """Send error update to frontend."""
        try:
            error_data = {
                'session_id': session_id,
                'error': error,
                'timestamp': time.time()
            }
            
            message = HLinkMessage(
                type=MessageType.TRANSCRIPTION_ERROR,
                sender=Sender(agent_id="whisper_pipeline", role="transcriber"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(
                    content="Transcription error",
                    session_id=session_id,
                    error=error
                )
            )
            
            await self.redis_client.publish_event("transcription_stream", json.loads(message.model_dump_json()))
            
        except Exception as e:
            logger.error(f"Failed to send error update: {e}")
    
    async def process_audio_request(self, session_id: str, audio_data: bytes):
        """Public interface for audio processing requests."""
        try:
            # Put raw bytes in queue
            self.transcription_queue.put((session_id, audio_data))
            
        except Exception as e:
            logger.error(f"Failed to process audio request: {e}")
            await self._send_error_update(session_id, str(e))
    
    async def start_session(self, session_id: str):
        """Start a new transcription session."""
        self.active_sessions[session_id] = {
            'start_time': time.time(),
            'chunks_processed': 0,
            'total_duration': 0.0,
            'last_update': time.time()
        }
        
        logger.info(f"Started transcription session: {session_id}")
        
        return {
            'session_id': session_id,
            'status': 'started',
            'device': self.device,
            'model_size': self.model_size
        }
    
    async def end_session(self, session_id: str):
        """End a transcription session and return final summary."""
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return None
        
        session_data = self.active_sessions[session_id]
        session_data['end_time'] = time.time()
        session_data['duration'] = session_data['total_duration']
        session_data['status'] = 'ended'
        
        logger.info(f"Ended transcription session: {session_id}, duration: {session_data['duration']:.1f}s")
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        return session_data
    
    def get_metrics(self):
        """Get current processing metrics."""
        return self.metrics
    
    def get_status(self):
        """Get current service status."""
        return {
            'initialized': self.is_initialized,
            'processing': self.is_processing,
            'device': self.device,
            'model_size': self.model_size,
            'active_sessions': len(self.active_sessions),
            'metrics': self.metrics
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        self.is_processing = False
        
        if self.processing_thread and self.processing_thread.is_alive():
            logger.info("Stopping Whisper processing loop...")
            # Signal thread to stop
            self.transcription_queue.put(None)  # Signal to exit
        
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        # Clear queues
        while not self.transcription_queue.empty():
            try:
                self.transcription_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        logger.info("Whisper service cleanup completed")
        
        if self.model:
            del self.model
            self.model = None
        
        self.is_initialized = False


# Global service instance
whisper_service = None

# Main interface function for WebSocket integration
async def handle_whisper_request(websocket, message: Dict[str, Any], redis_client):
    """Handle Whisper-related WebSocket messages."""
    global whisper_service
    try:
        # Initialize Whisper service if not already done
        if not whisper_service:
            whisper_service = WhisperService(redis_client)
            await whisper_service.initialize()
        
        message_type = message.get('type')
        
        if message_type == 'whisper_session_start':
            session_data = await whisper_service.start_session(
                message.get('payload', {}).get('session_id', 'default')
            )
            await websocket.send_text(json.dumps(session_data))
            
        elif message_type == 'whisper_session_end':
            session_data = await whisper_service.end_session(
                message.get('payload', {}).get('session_id', 'default')
            )
            await websocket.send_text(json.dumps(session_data))
            
        elif message_type == 'whisper_audio_data':
            await whisper_service.process_audio_request(
                message.get('payload', {}).get('session_id', 'default'),
                message.get('payload', {}).get('audio_data', b'')
            )
            
        elif message_type == 'whisper_status':
            status = whisper_service.get_status()
            # STORY 14.3 FIX: Wrap status in HLink message so frontend can route it
            response = HLinkMessage(
                type=MessageType.TRANSCRIPTION_STATUS,
                sender=Sender(agent_id="whisper_service", role="system"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(
                    content=status,
                    status="ready" if status['initialized'] else "initializing"
                )
            )
            await websocket.send_text(response.model_dump_json())
            
        else:
            logger.warning(f"Unknown Whisper message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Whisper request handling failed: {e}")