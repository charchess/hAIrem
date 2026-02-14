import logging
import numpy as np
from typing import Optional
import io

logger = logging.getLogger(__name__)

RESEMBLYZER_AVAILABLE = False
try:
    from resemblyzer import VoiceEncoder
    RESEMBLYZER_AVAILABLE = True
except ImportError:
    logger.warning("resemblyzer not available, voice recognition will use fallback mode")

PYANNOTE_AVAILABLE = False
try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    logger.warning("pyannote.audio not available, voice recognition will use fallback mode")


class VoiceEmbeddingExtractor:
    def __init__(self):
        self.encoder = None
        self.pipeline = None
        self._initialize()

    def _initialize(self):
        if RESEMBLYZER_AVAILABLE:
            try:
                self.encoder = VoiceEncoder()
                logger.info("VoiceEmbeddingExtractor initialized with resemblyzer")
            except Exception as e:
                logger.error(f"Failed to initialize resemblyzer encoder: {e}")
                self.encoder = None

        if PYANNOTE_AVAILABLE:
            try:
                logger.info("pyannote.audio available for speaker diarization")
            except Exception as e:
                logger.error(f"Failed to initialize pyannote pipeline: {e}")
                self.pipeline = None

    def extract_embedding(self, audio_data: bytes) -> Optional[list[float]]:
        if self.encoder is None:
            return self._extract_fallback_embedding(audio_data)

        try:
            audio_np = self._bytes_to_audio(audio_data)
            if audio_np is None or len(audio_np) == 0:
                logger.warning("No valid audio data provided")
                return None

            embedding = self.encoder.embed_utterance(audio_np)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to extract embedding: {e}")
            return self._extract_fallback_embedding(audio_data)

    def _bytes_to_audio(self, audio_data: bytes) -> Optional[np.ndarray]:
        try:
            import wave
            with wave.open(io.BytesIO(audio_data), 'rb') as wav:
                frames = wav.readframes(wav.getnframes())
                audio_np = np.frombuffer(frames, dtype=np.int16)
                audio_np = audio_np.astype(np.float32) / 32768.0
                return audio_np
        except Exception as e:
            logger.error(f"Failed to parse audio data: {e}")
            return None

    def _extract_fallback_embedding(self, audio_data: bytes) -> Optional[list[float]]:
        try:
            audio_np = self._bytes_to_audio(audio_data)
            if audio_np is None or len(audio_np) == 0:
                return None

            if len(audio_np) > 16000:
                num_chunks = len(audio_np) // 16000
                chunk_size = len(audio_np) // num_chunks
                features = []
                for i in range(num_chunks):
                    chunk = audio_np[i * chunk_size:(i + 1) * chunk_size]
                    chunk_features = self._extract_simple_features(chunk)
                    features.append(chunk_features)
                return np.mean(features, axis=0).tolist()
            else:
                return self._extract_simple_features(audio_np).tolist()
        except Exception as e:
            logger.error(f"Fallback embedding extraction failed: {e}")
            return None

    def _extract_simple_features(self, audio_np: np.ndarray) -> np.ndarray:
        features = []
        frame_length = 512
        hop_length = 256

        num_frames = max(1, (len(audio_np) - frame_length) // hop_length)
        for i in range(min(num_frames, 40)):
            start = i * hop_length
            frame = audio_np[start:start + frame_length]
            if len(frame) < frame_length:
                frame = np.pad(frame, (0, frame_length - len(frame)))

            rms = np.sqrt(np.mean(frame ** 2))
            features.append(rms)

            fft = np.fft.rfft(frame)
            spectral_centroid = np.sum(np.arange(len(fft)) * np.abs(fft)) / (np.sum(np.abs(fft)) + 1e-10)
            features.append(spectral_centroid)

        while len(features) < 80:
            features.append(0.0)

        return np.array(features[:80])

    def is_available(self) -> bool:
        return self.encoder is not None or RESEMBLYZER_AVAILABLE
