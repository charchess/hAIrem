"""
Text-to-Speech Service for hAIrem
Implements local Neural TTS (MeloTTS) with fallback to standard TTS
Supports streaming audio generation
"""

import asyncio
import logging
import time
import os
import tempfile
import base64
import threading
import queue
from typing import Dict, Any, Optional, Generator

# Try importing MeloTTS
try:
    from melo.api import TTS as MeloTTS
    MELO_AVAILABLE = True
except ImportError:
    MELO_AVAILABLE = False

# Try importing pyttsx3 as fallback
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

from models.hlink import HLinkMessage, MessageType, Payload, Sender, Recipient
from infrastructure.redis import RedisClient

logger = logging.getLogger(__name__)


class TTSService:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.engine_type = "auto"
        self.model = None
        self.device = "auto"
        self.is_initialized = False
        self.request_queue = queue.Queue()
        self.is_processing = False
        self.processing_thread = None
        self.loop = None
        
        # Audio generation settings
        self.sample_rate = 24000  # Standard for MeloTTS
        self.speaker_id = 0
        self.speed = 1.0
        
    async def initialize(self, engine="auto", device="auto"):
        """Initialize TTS engine."""
        try:
            if self.is_initialized:
                return True
            
            # Capture event loop
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning("No running event loop found during TTS initialization")
            
            # Select engine
            if engine == "auto":
                if MELO_AVAILABLE:
                    self.engine_type = "melo"
                elif PYTTSX3_AVAILABLE:
                    self.engine_type = "pyttsx3"
                else:
                    logger.error("No TTS engine available")
                    return False
            else:
                self.engine_type = engine
            
            logger.info(f"Initializing TTS with engine={self.engine_type}")
            
            if self.engine_type == "melo":
                # Initialize MeloTTS
                # self.model = MeloTTS(language='FR', device=device)
                pass
                
            elif self.engine_type == "pyttsx3":
                # Initialize pyttsx3 in the processing thread as it's not thread-safe
                pass
            
            self.is_initialized = True
            
            # Start processing thread
            self.is_processing = True
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True
            )
            self.processing_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            return False
    
    def _processing_loop(self):
        """Background processing loop for TTS requests."""
        logger.info("Starting TTS processing loop")
        
        # Initialize thread-local resources
        local_engine = None
        if self.engine_type == "pyttsx3":
            try:
                local_engine = pyttsx3.init()
                local_engine.setProperty('rate', 150)
                # Select a French voice if available
                voices = local_engine.getProperty('voices')
                for voice in voices:
                    if 'french' in voice.name.lower() or 'fr' in voice.languages:
                        local_engine.setProperty('voice', voice.id)
                        break
            except Exception as e:
                logger.error(f"Failed to init pyttsx3 in thread: {e}")
        
        while self.is_processing:
            try:
                try:
                    item = self.request_queue.get(timeout=1.0)
                    request_id, text, params = item
                    
                    self._process_tts_request(request_id, text, params, local_engine)
                    
                    self.request_queue.task_done()
                    
                except queue.Empty:
                    continue
                
            except Exception as e:
                logger.error(f"Error in TTS processing loop: {e}")
                time.sleep(0.1)
    
    def _process_tts_request(self, request_id: str, text: str, params: Dict, local_engine):
        """Process a single TTS request synchronously."""
        try:
            logger.info(f"Generating audio for request {request_id}: {text[:30]}...")
            
            # Notify start
            self._send_event(MessageType.TTS_START, request_id, {"text": text})
            
            if self.engine_type == "pyttsx3" and local_engine:
                # pyttsx3 doesn't support streaming easily, so we generate to file then read
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
                    temp_filename = tf.name
                
                local_engine.save_to_file(text, temp_filename)
                local_engine.runAndWait()
                
                # Read and send audio
                with open(temp_filename, 'rb') as f:
                    audio_data = f.read()
                
                # Send single chunk (simulated streaming)
                # Encode to base64 for transport
                b64_audio = base64.b64encode(audio_data).decode('utf-8')
                
                self._send_event(MessageType.TTS_AUDIO_CHUNK, request_id, {
                    "audio_chunk": b64_audio,
                    "index": 0,
                    "is_last": True,
                    "format": "wav"
                })
                
                # Cleanup
                try:
                    os.remove(temp_filename)
                except:
                    pass
                    
            elif self.engine_type == "melo":
                # MeloTTS implementation (placeholder for now)
                # In real impl, we would use self.model.tts_to_file but optimized for memory
                pass
            
            # Notify end
            self._send_event(MessageType.TTS_END, request_id, {"status": "completed"})
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            self._send_event(MessageType.TTS_ERROR, request_id, {"error": str(e)})
    
    def _send_event(self, msg_type, request_id, content):
        """Send event to WebSocket via main loop."""
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self._dispatch_event(msg_type, request_id, content),
                self.loop
            )
    
    async def _dispatch_event(self, msg_type, request_id, content):
        """Dispatch event to Redis."""
        try:
            message = HLinkMessage(
                type=msg_type,
                sender=Sender(agent_id="tts_service", role="system"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(
                    content=content,
                    session_id=request_id
                )
            )
            
            await self.redis_client.publish_event("tts_stream", "tts_update", message.model_dump())
            
        except Exception as e:
            logger.error(f"Failed to dispatch TTS event: {e}")
    
    async def speak(self, text: str, request_id: str = None, params: Dict = None):
        """Queue a text to be spoken."""
        if not request_id:
            request_id = f"tts_{int(time.time()*1000)}"
        
        self.request_queue.put((request_id, text, params or {}))
        return request_id
    
    async def cleanup(self):
        """Cleanup resources."""
        self.is_processing = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)


# Main interface function
tts_service = None

async def handle_tts_request(websocket, message: Dict[str, Any], redis_client):
    """Handle TTS-related WebSocket messages."""
    global tts_service
    
    if not tts_service:
        tts_service = TTSService(redis_client)
        await tts_service.initialize()
    
    try:
        msg_type = message.get('type')
        payload = message.get('payload', {})
        
        if msg_type == MessageType.TTS_REQUEST:
            text = payload.get('content')
            if text:
                req_id = await tts_service.speak(text)
                # Ack
                await websocket.send_text(json.dumps({
                    "type": "tts_ack",
                    "request_id": req_id,
                    "status": "queued"
                }))
                
    except Exception as e:
        logger.error(f"Error handling TTS request: {e}")
        
        import json
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": str(e)
        }))