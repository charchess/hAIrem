import logging
from typing import Optional

from .models import (
    VoiceProfile,
    VoiceIdentificationResult,
    VoiceEnrollmentRequest,
    VoiceIdentificationRequest,
    SessionUser,
)
from .embedding import VoiceEmbeddingExtractor
from .matcher import VoiceMatcher
from .repository import VoiceProfileRepository
from .fallback import VoiceRecognitionFallback
from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient

logger = logging.getLogger(__name__)


class VoiceRecognitionService:
    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        surreal_client: Optional[SurrealDbClient] = None,
        similarity_threshold: float = 0.75,
    ):
        self.redis = redis_client
        self.repository = VoiceProfileRepository(surreal_client)
        self.extractor = VoiceEmbeddingExtractor()
        self.matcher = VoiceMatcher(similarity_threshold=similarity_threshold)
        self.fallback = VoiceRecognitionFallback()

    async def enroll_voice(
        self,
        request: VoiceEnrollmentRequest
    ) -> VoiceProfile:
        embedding = self.extractor.extract_embedding(request.audio_data)

        if embedding is None:
            logger.warning(f"Failed to extract embedding for user {request.user_id}")
            embedding = []

        profile = VoiceProfile(
            user_id=request.user_id,
            name=request.name,
            embedding=embedding,
            sample_count=1,
        )

        await self.repository.save_profile(profile)

        logger.info(f"Voice enrolled for user: {request.user_id}")
        return profile

    async def identify_voice(
        self,
        request: VoiceIdentificationRequest
    ) -> VoiceIdentificationResult:
        embedding = self.extractor.extract_embedding(request.audio_data)

        if embedding is None:
            logger.warning("Failed to extract embedding from audio")
            return VoiceIdentificationResult(
                identified=False,
                confidence=0.0,
            )

        profiles = await self.repository.get_all_profiles()

        if not profiles:
            logger.info("No voice profiles available for matching")
            return VoiceIdentificationResult(
                identified=False,
                confidence=0.0,
                embedding=embedding,
            )

        matched_profile, confidence = self.matcher.find_best_match(
            embedding,
            profiles
        )

        if matched_profile:
            logger.info(f"Voice identified: user_id={matched_profile.get('user_id')}, confidence={confidence:.2f}")

            if self.redis:
                await self.redis.publish_event(
                    "voice.identified",
                    {
                        "session_id": request.session_id,
                        "user_id": matched_profile.get("user_id"),
                        "user_name": matched_profile.get("name"),
                        "confidence": confidence,
                    }
                )

            return VoiceIdentificationResult(
                identified=True,
                user_id=matched_profile.get("user_id"),
                user_name=matched_profile.get("name"),
                confidence=confidence,
                matched_profile=VoiceProfile(**matched_profile),
                embedding=embedding,
            )

        logger.info(f"Voice not identified, confidence={confidence:.2f}")
        return VoiceIdentificationResult(
            identified=False,
            confidence=confidence,
            embedding=embedding,
        )

    async def process_session_voice(
        self,
        session_id: str,
        audio_data: bytes
    ) -> SessionUser:
        result = await self.identify_voice(
            VoiceIdentificationRequest(
                session_id=session_id,
                audio_data=audio_data
            )
        )

        return self.fallback.handle_unidentified_voice(session_id, result)

    async def manual_identify(
        self,
        session_id: str,
        user_id: str,
        user_name: Optional[str] = None
    ) -> SessionUser:
        result = self.fallback.manual_identify(session_id, user_id, user_name)

        if self.redis:
            await self.redis.publish_event(
                "voice.manual_identify",
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "user_name": user_name,
                }
            )

        return result

    def get_session_user(self, session_id: str) -> Optional[SessionUser]:
        return self.fallback.get_session_user(session_id)

    def create_anonymous_session(self, session_id: str) -> SessionUser:
        return self.fallback.create_anonymous_session(session_id)

    def is_extractor_available(self) -> bool:
        return self.extractor.is_available()
