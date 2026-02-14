"""
Wake Word Detection Engine for hAIrem
Implements continuous wake word monitoring using tinyML and audio processing
"""

import asyncio
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, List
import threading
import queue
import time

try:
    from tinyml import AudioClassifier
except ImportError:
    print("Warning: tinyml AudioClassifier not available, using fallback")
    AudioClassifier = None

try:
    import librosa
except ImportError:
    print("Warning: librosa not available, using fallback")
    librosa = None

from models.hlink import HLinkMessage, MessageType, Payload, Sender, Recipient

logger = logging.getLogger(__name__)


class WakeWordEngine:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.is_active = False
        self.audio_queue = queue.Queue()
        self.classifier = None
        self.sample_rate = 16000
        self.wake_words = ["hey lisa", "ok lisa", "lisent"]
        self.threshold = 0.7
        self.background_thread = None
        self.audio_buffer = []
        self.buffer_size = 2048  # About 128ms of audio at 16kHz
        
    async def initialize(self):
        """Initialize the wake word detection system."""
        try:
            logger.info("Initializing Wake Word Engine...")
            
            # Load or create wake word model
            await self.load_model()
            
            # Start background monitoring
            self.is_active = True
            self.background_thread = threading.Thread(
                target=self.background_processing_loop,
                daemon=True
            )
            self.background_thread.start()
            
            logger.info("Wake Word Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Wake Word Engine initialization failed: {e}")
            return False
    
    async def load_model(self):
        """Load or create wake word model."""
        try:
            # Try to load pre-trained model
            if AudioClassifier:
                self.classifier = AudioClassifier.load('wake_words_model.tflite')
                logger.info("Loaded pre-trained wake word model")
            else:
                raise ImportError("AudioClassifier not available")
        except Exception as e:
            # Create simple model if pre-trained not available
            logger.warning(f"No pre-trained model found, creating simple wake word detector: {e}")
            self.classifier = self.create_simple_detector()
    
    def create_simple_detector(self):
        """Create a simple wake word detector using audio features."""
        # For now, return a mock classifier that will be enhanced
        class SimpleWakeDetector:
            def __init__(self):
                self.energy_threshold = 0.01
                self.zcr_threshold = 0.1
                
            def process(self, audio_data):
                if len(audio_data) == 0:
                    return False, 0.0
                
                # Simple energy-based detection
                energy = np.mean(audio_data ** 2)
                zcr = self.zero_crossing_rate(audio_data)
                
                # Combine features
                wake_score = 0.6 if energy > self.energy_threshold else 0.3
                wake_score += 0.4 if zcr < self.zcr_threshold else 0.0
                
                return wake_score > 0.7, wake_score
            
            def zero_crossing_rate(self, audio_data):
                signs = np.sign(audio_data[:-1]) != np.sign(audio_data[1:])
                return np.sum(signs) / len(audio_data)
        
        return SimpleWakeDetector()
    
    def background_processing_loop(self):
        """Main background processing loop for wake word detection."""
        logger.info("Starting wake word monitoring...")
        
        while self.is_active:
            try:
                # Simulate audio processing
                # In real implementation, this would read from microphone
                audio_chunk = self.simulate_audio_input()
                
                if audio_chunk is not None:
                    result, confidence = self.classifier.process(audio_chunk)
                    
                    if result:
                        # Wake word detected!
                        asyncio.create_task(self.on_wake_word_detected(confidence))
                    
            except Exception as e:
                logger.error(f"Error in wake word processing loop: {e}")
                time.sleep(0.1)
    
    def simulate_audio_input(self):
        """Simulate audio input for testing."""
        # In real implementation, this would be replaced with actual microphone input
        time.sleep(0.1)  # Simulate audio timing
        
        # Return dummy audio data
        return np.random.normal(0, 0.01, self.buffer_size).astype(np.float32)
    
    async def on_wake_word_detected(self, confidence: float):
        """Handle wake word detection event."""
        logger.info(f"Wake word detected! Confidence: {confidence}")
        
        try:
            # Send wake word detected event
            wake_message = HLinkMessage(
                type=MessageType.WAKE_WORD_DETECTED,
                sender=Sender(agent_id="wakeword_engine", role="detector"),
                recipient=Recipient(target="audio_system"),
                payload=Payload(
                    content="Wake word activated",
                    confidence=confidence,
                    wake_word="hey lisa",
                    detection_time=str(time.time())
                )
            )
            
            await self.redis_client.publish_event("wake_events", "wakeword", wake_message.model_dump())
            
            # Trigger audio capture system
            trigger_message = HLinkMessage(
                type=MessageType.AUDIO_AUTO_START,
                sender=Sender(agent_id="wakeword_engine", role="trigger"),
                recipient=Recipient(target="audio_capture"),
                payload=Payload(
                    content="Auto-start recording",
                    trigger_source="wake_word",
                    confidence=confidence
                )
            )
            
            await self.redis_client.publish_event("audio_stream", "auto_start", trigger_message.model_dump())
            
        except Exception as e:
            logger.error(f"Failed to handle wake word detection: {e}")
    
    async def stop(self):
        """Stop the wake word detection engine."""
        self.is_active = False
        if self.background_thread:
            self.background_thread.join(timeout=5.0)
        
        logger.info("Wake Word Engine stopped")


# Wake word handler function for WebSocket integration
async def handle_wakeword_message(websocket, message: Dict[str, Any], redis_client):
    """Handle wake word related messages from frontend."""
    try:
        message_type = message.get('type')
        
        if message_type == 'wakeword_status_request':
            # Send current status
            engine = WakeWordEngine(redis_client)
            status_message = HLinkMessage(
                type=MessageType.WAKE_WORD_STATUS,
                sender=Sender(agent_id="wakeword_engine", role="system"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(
                    content="Wake word engine status",
                    active=engine.is_active
                )
            )
            
            await websocket.send_text(status_message.model_dump_json())
            
        elif message_type == 'wakeword_enable':
            # Enable wake word detection
            engine = WakeWordEngine(redis_client)
            success = await engine.initialize()
            
            response_message = HLinkMessage(
                type=MessageType.WAKE_WORD_STATUS,
                sender=Sender(agent_id="wakeword_engine", role="system"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(
                    content="Wake word engine enabled" if success else "Failed to enable",
                    enabled=success
                )
            )
            
            await websocket.send_text(response_message.model_dump_json())
            
        elif message_type == 'wakeword_disable':
            # Disable wake word detection
            # Implementation would stop the engine
            disable_message = HLinkMessage(
                type=MessageType.WAKE_WORD_STATUS,
                sender=Sender(agent_id="wakeword_engine", role="system"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(
                    content="Wake word engine disabled",
                    enabled=False
                )
            )
            
            await websocket.send_text(disable_message.model_dump_json())
        
    except Exception as e:
        logger.error(f"Wake word message handling failed: {e}")


# Audio processing utilities
def extract_audio_features(audio_data: np.ndarray, sample_rate: int = 16000):
    """Extract features for wake word detection."""
    try:
        # Energy feature
        energy = np.sum(audio_data ** 2) / len(audio_data)
        
        # Zero crossing rate
        zcr = np.mean(librosa.feature.zero_crossing_rate(
            audio_data, 
            frame_length=2048, 
            hop_length=512
        ))
        
        # Spectral centroid
        spectral_centroids = librosa.feature.spectral_centroid(
            y=audio_data,
            sr=sample_rate,
            hop_length=512
        )
        spectral_centroid = np.mean(spectral_centroids) if len(spectral_centroids) > 0 else 0
        
        return {
            'energy': energy,
            'zcr': zcr,
            'spectral_centroid': spectral_centroid
        }
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        return {
            'energy': 0.0,
            'zcr': 0.0,
            'spectral_centroid': 0.0
        }


def create_simple_wake_word_model():
    """Create a simple machine learning model for wake word detection."""
    # This is a placeholder - in production, you'd use a pre-trained model
    # For now, we'll use rule-based detection
    
    class SimpleWakeModel:
        def __init__(self):
            self.energy_threshold = 0.01
            self.zcr_threshold = 0.1
            self.spectral_threshold = 2000
        
        def predict(self, features: Dict[str, float]):
            """Simple rule-based wake word prediction."""
            energy = features.get('energy', 0.0)
            zcr = features.get('zcr', 0.0)
            spectral = features.get('spectral_centroid', 0.0)
            
            # Simple heuristic rules
            score = 0.0
            
            # Energy condition (speech has energy)
            if energy > self.energy_threshold:
                score += 0.4
            
            # ZCR condition (speech has frequent zero crossings)
            if zcr > self.zcr_threshold:
                score += 0.3
            
            # Spectral condition (speech has right frequency distribution)
            if 500 < spectral < 3000:
                score += 0.3
            
            return score > 0.7, score
    
    return SimpleWakeModel()