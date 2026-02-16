"""
Wakeword Engine for hAIrem
Implements wakeword detection using openWakeWord library.
Supports "Hey Lisa" wakeword for voice activation.
"""

import asyncio
import logging
import numpy as np
import queue
import threading
import time
from typing import Optional, Callable, Dict, Any
import wave

try:
    import pyaudio

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logging.warning("pyaudio not available, wakeword detection disabled")

try:
    from openwakeword import Model

    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False
    logging.warning("openWakeWord not available, wakeword detection disabled")

logger = logging.getLogger(__name__)


class WakewordEngine:
    """
    Wakeword detection engine using openWakeWord.
    Detects "Hey Lisa" to activate voice interaction.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model: Optional[Model] = None
        self.audio: Optional[pyaudio.PyAudio] = None
        self.audio_stream = None
        self.is_running = False
        self.detection_callback: Optional[Callable] = None
        self.audio_queue = queue.Queue(maxsize=100)
        self.processing_thread: Optional[threading.Thread] = None
        self.capture_thread: Optional[threading.Thread] = None

        # Wakeword configuration
        self.wakeword = config.get("wakeword", "hey_lisa")
        self.threshold = config.get("threshold", 0.5)
        self.chunk_size = config.get("chunk_size", 1280)  # 80ms at 16kHz
        self.sample_rate = 16000
        self.channels = 1

        if not OPENWAKEWORD_AVAILABLE or not PYAUDIO_AVAILABLE:
            logger.error("Cannot initialize WakewordEngine: required libraries not available")
            return

        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()

            # Initialize openWakeWord model
            self.model = Model(wakeword_models=[self.wakeword], enable_speex_noise_suppression=True)
            logger.info(f"WakewordEngine initialized with wakeword: {self.wakeword}")
        except Exception as e:
            logger.error(f"Failed to initialize wakeword model: {e}")
            self.model = None
            if self.audio:
                self.audio.terminate()

    async def start_listening(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """
        Start listening for wakeword detection.

        Args:
            callback: Function to call when wakeword is detected

        Returns:
            bool: True if started successfully
        """
        if not self.model or not self.audio:
            logger.error("Cannot start listening: wakeword model or audio not initialized")
            return False

        if self.is_running:
            logger.warning("Wakeword engine already running")
            return True

        self.detection_callback = callback

        try:
            # Open audio stream
            self.audio_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback,
            )

            # Start audio stream
            self.audio_stream.start_stream()

            # Start processing thread
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()

            logger.info("Wakeword detection started")
            return True

        except Exception as e:
            logger.error(f"Failed to start wakeword detection: {e}")
            return False

        if self.is_running:
            logger.warning("Wakeword engine already running")
            return True

        self.detection_callback = callback

        try:
            # Initialize audio stream
            self.audio_stream = AudioStream(sample_rate=16000, channels=1, chunk_size=self.chunk_size)

            # Start audio capture
            await self.audio_stream.start()

            # Start processing thread
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()

            logger.info("Wakeword detection started")
            return True

        except Exception as e:
            logger.error(f"Failed to start wakeword detection: {e}")
            return False

    async def stop_listening(self) -> None:
        """Stop wakeword detection."""
        if not self.is_running:
            return

        self.is_running = False

        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()

        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)

        if self.audio:
            self.audio.terminate()

        logger.info("Wakeword detection stopped")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for audio data."""
        if not self.is_running:
            return (None, pyaudio.paContinue)

        try:
            # Convert audio data to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.int16)

            # Convert to float32 for openWakeWord
            audio_float = audio_data.astype(np.float32) / 32768.0

            # Add to processing queue
            if not self.audio_queue.full():
                self.audio_queue.put(audio_float)
            else:
                logger.warning("Audio queue full, dropping audio chunk")

        except Exception as e:
            logger.error(f"Error in audio callback: {e}")

        return (None, pyaudio.paContinue)

    def _processing_loop(self) -> None:
        """Main processing loop for wakeword detection."""
        while self.is_running:
            try:
                # Get audio chunk
                audio_data = self.audio_queue.get(timeout=0.1)
                if audio_data is None:
                    continue

                # Predict wakeword
                prediction = self.model.predict(audio_data)

                # Check for wakeword detection
                wakeword_prediction = prediction.get(self.wakeword, 0.0)
                if wakeword_prediction > self.threshold:
                    # Wakeword detected!
                    detection_info = {
                        "wakeword": self.wakeword,
                        "confidence": wakeword_prediction,
                        "timestamp": time.time(),
                    }

                    # Call callback in main thread
                    if self.detection_callback:
                        asyncio.run(self.detection_callback(detection_info))

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in wakeword processing: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_listening()


class WakewordDetector:
    """
    High-level wakeword detector that manages the wakeword engine
    and integrates with the hAIrem event system.
    """

    def __init__(self, config: Dict[str, Any], event_bus):
        self.config = config
        self.event_bus = event_bus
        self.engine: Optional[WakewordEngine] = None

    async def initialize(self) -> bool:
        """Initialize the wakeword detector."""
        try:
            self.engine = WakewordEngine(self.config)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize wakeword detector: {e}")
            return False

    async def start_detection(self) -> bool:
        """Start wakeword detection."""
        if not self.engine:
            return False

        return await self.engine.start_listening(self._on_wakeword_detected)

    async def stop_detection(self) -> None:
        """Stop wakeword detection."""
        if self.engine:
            await self.engine.stop_listening()

    async def _on_wakeword_detected(self, detection_info: Dict[str, Any]) -> None:
        """Handle wakeword detection event."""
        logger.info(f"Wakeword detected: {detection_info}")

        # Publish wakeword detected event
        await self.event_bus.publish(
            {"type": "wakeword.detected", "data": detection_info, "timestamp": detection_info["timestamp"]}
        )

    async def get_status(self) -> Dict[str, Any]:
        """Get current status of wakeword detection."""
        return {
            "active": self.engine is not None and self.engine.is_running,
            "wakeword": self.config.get("wakeword", "hey_lisa"),
            "threshold": self.config.get("threshold", 0.5),
        }
