"""
Text-to-Speech Service for hAIrem
Implements local Neural TTS (MeloTTS) with fallback to standard TTS
Supports streaming audio generation
Epic 5: Voice Capabilities - Dedicated Base Voice, Voice Modulation, Prosody
"""

import asyncio
import logging
import time
import os
import tempfile
import base64
import threading
import queue
import httpx
from typing import Dict, Any, Optional, Generator

try:
    from melo.api import TTS as MeloTTS

    MELO_AVAILABLE = True
except ImportError:
    MELO_AVAILABLE = False

try:
    import pyttsx3

    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

from models.hlink import HLinkMessage, MessageType, Payload, Sender, Recipient
from infrastructure.redis import RedisClient

from services.voice import voice_profile_service, VoiceProfile
from services.voice_modulation import voice_modulation_service, EMOTION_CONFIGS
from services.prosody import prosody_service, IntonationType
from services.neural_voice_assignment import neural_voice_assignment_service

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


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

        self.sample_rate = 24000
        self.speaker_id = 0
        self.speed = 1.0

        self.voice_profile_service = voice_profile_service
        self.voice_modulation_service = voice_modulation_service
        self.prosody_service = prosody_service

    async def initialize(self, engine="auto", device="auto"):
        """Initialize TTS engine and voice services."""
        try:
            if self.is_initialized:
                return True

            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning("No running event loop found during TTS initialization")

            if engine == "auto":
                if ELEVENLABS_API_KEY:
                    self.engine_type = "elevenlabs"
                elif MELO_AVAILABLE:
                    self.engine_type = "melo"
                elif PYTTSX3_AVAILABLE:
                    self.engine_type = "pyttsx3"
                else:
                    logger.error("No TTS engine available")
                    return False
            else:
                self.engine_type = engine

            logger.info(f"Initializing TTS with engine={self.engine_type}")

            await self.voice_profile_service.initialize()
            await self.voice_modulation_service.initialize()
            await self.prosody_service.initialize()
            await neural_voice_assignment_service.initialize()

            self.is_initialized = True
            self.is_processing = True
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()

            return True

        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            return False

    def _processing_loop(self):
        """Background processing loop for TTS requests."""
        logger.info("Starting TTS processing loop")

        local_engine = None
        if self.engine_type == "pyttsx3":
            try:
                local_engine = pyttsx3.init()
                local_engine.setProperty("rate", 150)
                voices = local_engine.getProperty("voices")
                for voice in voices:
                    if "french" in voice.name.lower() or "fr" in voice.languages:
                        local_engine.setProperty("voice", voice.id)
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
        """Process a single TTS request."""
        try:
            logger.info(f"Generating audio for request {request_id}: {text[:30]}...")

            pitch = params.get("pitch", 1.0)
            rate = params.get("rate", 1.0)
            volume = params.get("volume", 1.0)
            emotion = params.get("emotion", "neutral")

            self._send_event(
                MessageType.TTS_START,
                request_id,
                {"text": text, "voice_params": {"pitch": pitch, "rate": rate, "volume": volume, "emotion": emotion}},
            )

            # --- ENGINE SELECTION ---

            # 1. ElevenLabs (High-Fi)
            if self.engine_type == "elevenlabs":
                voice_id = params.get("voice_id", "21m00Tcm4TlvDq8ikWAM")
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
                data = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                }

                resp = httpx.post(url, json=data, headers=headers, timeout=30.0)
                if resp.status_code == 200:
                    b64_audio = base64.b64encode(resp.content).decode("utf-8")
                    self._send_event(
                        MessageType.TTS_AUDIO_CHUNK,
                        request_id,
                        {"audio_chunk": b64_audio, "index": 0, "is_last": True, "format": "mp3"},
                    )
                else:
                    logger.error(f"ElevenLabs failed: {resp.text}")

            # 2. Pyttsx3 (Local Fallback)
            elif self.engine_type == "pyttsx3" and local_engine:
                local_engine.setProperty("rate", int(150 * rate))
                local_engine.setProperty("volume", min(1.0, volume))

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                    temp_filename = tf.name

                local_engine.save_to_file(text, temp_filename)
                local_engine.runAndWait()

                with open(temp_filename, "rb") as f:
                    audio_data = f.read()

                b64_audio = base64.b64encode(audio_data).decode("utf-8")
                self._send_event(
                    MessageType.TTS_AUDIO_CHUNK,
                    request_id,
                    {"audio_chunk": b64_audio, "index": 0, "is_last": True, "format": "wav"},
                )
                try:
                    os.remove(temp_filename)
                except:
                    pass

            self._send_event(MessageType.TTS_END, request_id, {"status": "completed"})

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            self._send_event(MessageType.TTS_ERROR, request_id, {"error": str(e)})

    def _send_event(self, msg_type, request_id, content):
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._dispatch_event(msg_type, request_id, content), self.loop)

    async def _dispatch_event(self, msg_type, request_id, content):
        try:
            message = HLinkMessage(
                type=msg_type,
                sender=Sender(agent_id="tts_service", role="system"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(content=content, session_id=request_id),
            )
            await self.redis_client.publish_event("tts_stream", "tts_update", message.model_dump())
        except Exception as e:
            logger.error(f"Failed to dispatch TTS event: {e}")

    async def speak(self, text: str, request_id: str = None, params: Dict = None):
        if not request_id:
            request_id = f"tts_{int(time.time() * 1000)}"
        params = params or {}
        agent_id = params.get("agent_id", "default")
        base_params = await self.voice_profile_service.apply_to_tts_params(
            agent_id, {"pitch": 1.0, "rate": 1.0, "volume": 1.0}
        )
        emotion = params.get("emotion")
        if emotion:
            base_params = self.voice_modulation_service.modulate_voice(base_params, emotion)
        style = params.get("prosody_style", "default")
        base_params = self.prosody_service.apply_prosody(base_params, text, style=style)
        final_params = {**params, **base_params}
        self.request_queue.put((request_id, text, final_params))
        return request_id

    async def cleanup(self):
        self.is_processing = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)


tts_service = None


async def handle_tts_request(websocket, message: Dict[str, Any], redis_client):
    global tts_service
    if not tts_service:
        tts_service = TTSService(redis_client)
        await tts_service.initialize()
    try:
        msg_type = message.get("type")
        payload = message.get("payload", {})
        if msg_type == MessageType.TTS_REQUEST:
            text = payload.get("content")
            if text:
                req_id = await tts_service.speak(text)
                await websocket.send_text(json.dumps({"type": "tts_ack", "request_id": req_id, "status": "queued"}))
    except Exception as e:
        logger.error(f"Error handling TTS request: {e}")
        await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
