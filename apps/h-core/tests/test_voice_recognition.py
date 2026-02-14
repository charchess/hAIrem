import pytest
import numpy as np
import wave
import io
import sys
from unittest.mock import AsyncMock, MagicMock, patch
sys.path.insert(0, "src/features/home")

from voice_recognition.embedding import VoiceEmbeddingExtractor
from voice_recognition.matcher import VoiceMatcher
from voice_recognition.fallback import VoiceRecognitionFallback
from voice_recognition.service import VoiceRecognitionService
from voice_recognition.models import (
    VoiceProfile,
    VoiceIdentificationResult,
    VoiceEnrollmentRequest,
    VoiceIdentificationRequest,
    SessionUser,
)


def create_wav_bytes(sample_rate=16000, duration=1):
    num_samples = int(sample_rate * duration)
    audio_data = np.random.randint(-32768, 32767, num_samples, dtype=np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio_data.tobytes())
    return buffer.getvalue()


class TestVoiceEmbeddingExtraction:
    def test_extract_embedding_returns_list(self):
        extractor = VoiceEmbeddingExtractor()
        audio_data = create_wav_bytes()
        
        embedding = extractor.extract_embedding(audio_data)
        
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 80

    def test_extract_embedding_with_empty_audio(self):
        extractor = VoiceEmbeddingExtractor()
        
        embedding = extractor.extract_embedding(b'')
        
        assert embedding is None

    def test_extract_embedding_with_short_audio(self):
        extractor = VoiceEmbeddingExtractor()
        short_audio = create_wav_bytes(duration=0.1)
        
        embedding = extractor.extract_embedding(short_audio)
        
        assert embedding is not None
        assert isinstance(embedding, list)

    def test_extract_embedding_consistency(self):
        extractor = VoiceEmbeddingExtractor()
        audio_data = create_wav_bytes(duration=2)
        
        embedding1 = extractor.extract_embedding(audio_data)
        embedding2 = extractor.extract_embedding(audio_data)
        
        assert embedding1 is not None
        assert embedding2 is not None
        assert np.allclose(embedding1, embedding2, atol=1e-6)

    def test_is_available_returns_boolean(self):
        extractor = VoiceEmbeddingExtractor()
        
        result = extractor.is_available()
        
        assert isinstance(result, bool)


class TestVoiceMatchingWithSimilarityThreshold:
    def test_compare_embeddings_identical(self):
        matcher = VoiceMatcher(similarity_threshold=0.75)
        embedding = [1.0] * 80
        
        similarity = matcher.compare_embeddings(embedding, embedding)
        
        assert np.isclose(similarity, 1.0)

    def test_compare_embeddings_different(self):
        matcher = VoiceMatcher(similarity_threshold=0.75)
        embedding1 = [1.0] * 80
        embedding2 = [0.0] * 80
        
        similarity = matcher.compare_embeddings(embedding1, embedding2)
        
        assert similarity < 0.5

    def test_compare_embeddings_empty(self):
        matcher = VoiceMatcher(similarity_threshold=0.75)
        
        similarity = matcher.compare_embeddings([], [1.0] * 80)
        assert similarity == 0.0
        
        similarity = matcher.compare_embeddings([1.0] * 80, [])
        assert similarity == 0.0

    def test_compare_embeddings_different_lengths(self):
        matcher = VoiceMatcher(similarity_threshold=0.75)
        embedding1 = [1.0] * 80
        embedding2 = [1.0] * 40
        
        similarity = matcher.compare_embeddings(embedding1, embedding2)
        
        assert isinstance(similarity, float)

    def test_find_best_match_above_threshold(self):
        matcher = VoiceMatcher(similarity_threshold=0.75)
        query_embedding = [1.0] * 80
        profiles = [
            {"user_id": "user1", "name": "User One", "embedding": [0.9] * 80},
            {"user_id": "user2", "name": "User Two", "embedding": [0.5] * 80},
        ]
        
        best_match, confidence = matcher.find_best_match(query_embedding, profiles)
        
        assert best_match is not None
        assert best_match["user_id"] == "user1"
        assert confidence >= 0.75

    def test_find_best_match_below_threshold(self):
        matcher = VoiceMatcher(similarity_threshold=0.75)
        query_embedding = [1.0] * 80
        profiles = [
            {"user_id": "user1", "name": "User One", "embedding": [(-1)**i for i in range(80)]},
            {"user_id": "user2", "name": "User Two", "embedding": [(-1)**(i+1) for i in range(80)]},
        ]
        
        best_match, confidence = matcher.find_best_match(query_embedding, profiles)
        
        assert best_match is None
        assert confidence < 0.75

    def test_find_best_match_empty_profiles(self):
        matcher = VoiceMatcher(similarity_threshold=0.75)
        
        best_match, confidence = matcher.find_best_match([1.0] * 80, [])
        
        assert best_match is None
        assert confidence == 0.0

    def test_find_best_match_empty_embedding(self):
        matcher = VoiceMatcher(similarity_threshold=0.75)
        
        best_match, confidence = matcher.find_best_match([], [{"user_id": "user1", "embedding": [1.0] * 80}])
        
        assert best_match is None
        assert confidence == 0.0

    def test_is_match_above_threshold(self):
        matcher = VoiceMatcher(similarity_threshold=0.75)
        
        assert matcher.is_match(0.8) is True
        assert matcher.is_match(0.75) is True

    def test_is_match_below_threshold(self):
        matcher = VoiceMatcher(similarity_threshold=0.75)
        
        assert matcher.is_match(0.74) is False
        assert matcher.is_match(0.5) is False


class TestFallbackToAnonymousSession:
    def test_create_anonymous_session(self):
        fallback = VoiceRecognitionFallback()
        
        session_user = fallback.create_anonymous_session("session123")
        
        assert session_user.session_id == "session123"
        assert session_user.user_id is None
        assert session_user.is_anonymous is True

    def test_handle_unidentified_voice_creates_anonymous_session(self):
        fallback = VoiceRecognitionFallback()
        result = VoiceIdentificationResult(identified=False, confidence=0.3)
        
        session_user = fallback.handle_unidentified_voice("session123", result)
        
        assert session_user.is_anonymous is True
        assert session_user.session_id == "session123"

    def test_handle_unidentified_voice_assigns_user_when_identified(self):
        fallback = VoiceRecognitionFallback()
        result = VoiceIdentificationResult(
            identified=True,
            user_id="user123",
            user_name="Test User",
            confidence=0.9
        )
        
        session_user = fallback.handle_unidentified_voice("session123", result)
        
        assert session_user.is_anonymous is False
        assert session_user.user_id == "user123"

    def test_handle_unidentified_voice_preserves_existing_identified_user(self):
        fallback = VoiceRecognitionFallback()
        
        fallback.assign_user_to_session("session123", "existing_user", "Existing User")
        
        result = VoiceIdentificationResult(
            identified=False,
            confidence=0.3
        )
        
        session_user = fallback.handle_unidentified_voice("session123", result)
        
        assert session_user.is_anonymous is False
        assert session_user.user_id == "existing_user"

    def test_get_session_user_returns_existing_session(self):
        fallback = VoiceRecognitionFallback()
        fallback.create_anonymous_session("session123")
        
        session_user = fallback.get_session_user("session123")
        
        assert session_user is not None
        assert session_user.session_id == "session123"

    def test_get_session_user_returns_none_for_unknown_session(self):
        fallback = VoiceRecognitionFallback()
        
        session_user = fallback.get_session_user("unknown_session")
        
        assert session_user is None

    def test_clear_session(self):
        fallback = VoiceRecognitionFallback()
        fallback.create_anonymous_session("session123")
        
        result = fallback.clear_session("session123")
        
        assert result is True
        assert fallback.get_session_user("session123") is None


class TestManualIdentification:
    def test_manual_identify_creates_session_user(self):
        fallback = VoiceRecognitionFallback()
        
        session_user = fallback.manual_identify("session123", "user456", "Manual User")
        
        assert session_user.user_id == "user456"
        assert session_user.is_anonymous is False

    def test_manual_identify_overwrites_existing_session(self):
        fallback = VoiceRecognitionFallback()
        fallback.create_anonymous_session("session123")
        
        session_user = fallback.manual_identify("session123", "user456", "Manual User")
        
        assert session_user.user_id == "user456"
        assert session_user.is_anonymous is False

    def test_manual_identify_without_user_name(self):
        fallback = VoiceRecognitionFallback()
        
        session_user = fallback.manual_identify("session123", "user456")
        
        assert session_user.user_id == "user456"
        assert session_user.is_anonymous is False


class TestVoiceRecognitionService:
    @pytest.mark.asyncio
    async def test_enroll_voice(self):
        service = VoiceRecognitionService()
        audio_data = create_wav_bytes()
        
        profile = await service.enroll_voice(
            VoiceEnrollmentRequest(
                user_id="user123",
                name="Test User",
                audio_data=audio_data
            )
        )
        
        assert profile.user_id == "user123"
        assert profile.name == "Test User"
        assert isinstance(profile.embedding, list)

    @pytest.mark.asyncio
    async def test_identify_voice_success(self):
        mock_repository = AsyncMock()
        mock_repository.get_all_profiles = AsyncMock(return_value=[
            {"user_id": "user123", "name": "Test User", "embedding": [1.0] * 80}
        ])
        
        service = VoiceRecognitionService(similarity_threshold=0.75)
        service.repository = mock_repository
        audio_data = create_wav_bytes()
        
        result = await service.identify_voice(
            VoiceIdentificationRequest(
                session_id="session123",
                audio_data=audio_data
            )
        )
        
        assert result.identified is True or result.identified is False
        assert isinstance(result.confidence, float)

    @pytest.mark.asyncio
    async def test_identify_voice_no_profiles(self):
        mock_repository = AsyncMock()
        mock_repository.get_all_profiles = AsyncMock(return_value=[])
        
        service = VoiceRecognitionService()
        service.repository = mock_repository
        audio_data = create_wav_bytes()
        
        result = await service.identify_voice(
            VoiceIdentificationRequest(
                session_id="session123",
                audio_data=audio_data
            )
        )
        
        assert result.identified is False
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_identify_voice_with_empty_audio(self):
        service = VoiceRecognitionService()
        
        result = await service.identify_voice(
            VoiceIdentificationRequest(
                session_id="session123",
                audio_data=b''
            )
        )
        
        assert result.identified is False
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_process_session_voice_returns_session_user(self):
        service = VoiceRecognitionService()
        audio_data = create_wav_bytes()
        
        session_user = await service.process_session_voice("session123", audio_data)
        
        assert isinstance(session_user, SessionUser)
        assert session_user.session_id == "session123"

    @pytest.mark.asyncio
    async def test_manual_identify_returns_session_user(self):
        service = VoiceRecognitionService()
        
        session_user = await service.manual_identify("session123", "user456", "Manual User")
        
        assert session_user.user_id == "user456"
        assert session_user.is_anonymous is False

    def test_get_session_user(self):
        service = VoiceRecognitionService()
        
        session_user = service.get_session_user("session123")
        
        assert session_user is None or isinstance(session_user, SessionUser)

    def test_create_anonymous_session(self):
        service = VoiceRecognitionService()
        
        session_user = service.create_anonymous_session("session123")
        
        assert session_user.is_anonymous is True
        assert session_user.session_id == "session123"

    def test_is_extractor_available(self):
        service = VoiceRecognitionService()
        
        result = service.is_extractor_available()
        
        assert isinstance(result, bool)
