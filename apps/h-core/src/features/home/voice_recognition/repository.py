import logging
from typing import Optional
from datetime import datetime

from .models import VoiceProfile
from src.infrastructure.surrealdb import SurrealDbClient

logger = logging.getLogger(__name__)


class VoiceProfileRepository:
    def __init__(self, surreal_client: Optional[SurrealDbClient] = None):
        self.surreal = surreal_client
        self._initialized = False

    async def initialize(self):
        if self._initialized or not self.surreal:
            return

        try:
            await self.surreal._call('query', """
                DEFINE TABLE IF NOT EXISTS voice_profile SCHEMAFULL;
                DEFINE FIELD IF NOT EXISTS user_id ON TABLE voice_profile TYPE string;
                DEFINE FIELD IF NOT EXISTS name ON TABLE voice_profile TYPE string;
                DEFINE FIELD IF NOT EXISTS embedding ON TABLE voice_profile TYPE array<float, 512>;
                DEFINE FIELD IF NOT EXISTS created_at ON TABLE voice_profile TYPE datetime;
                DEFINE FIELD IF NOT EXISTS updated_at ON TABLE voice_profile TYPE datetime;
                DEFINE FIELD IF NOT EXISTS sample_count ON TABLE voice_profile TYPE int DEFAULT 0;
                DEFINE FIELD IF NOT EXISTS is_active ON TABLE voice_profile TYPE bool DEFAULT true;
                DEFINE INDEX IF NOT EXISTS voice_user_id ON TABLE voice_profile FIELDS user_id UNIQUE;
            """)
            self._initialized = True
            logger.info("Voice profile schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize voice profile schema: {e}")

    async def save_profile(self, profile: VoiceProfile) -> bool:
        if not self.surreal:
            logger.warning("SurrealDB not available, using in-memory fallback")
            return False

        try:
            await self.initialize()

            existing = await self.get_by_user_id(profile.user_id)
            if existing:
                await self.surreal._call('query',
                    """
                    UPDATE voice_profile SET
                        embedding = $embedding,
                        name = $name,
                        updated_at = time::now(),
                        sample_count = sample_count + 1,
                        is_active = $is_active
                    WHERE user_id = $user_id
                    """,
                    {
                        "user_id": profile.user_id,
                        "name": profile.name,
                        "embedding": profile.embedding,
                        "is_active": profile.is_active
                    }
                )
            else:
                await self.surreal._call('create', 'voice_profile', {
                    "user_id": profile.user_id,
                    "name": profile.name,
                    "embedding": profile.embedding,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "sample_count": 1,
                    "is_active": True
                })

            logger.info(f"Voice profile saved for user: {profile.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save voice profile: {e}")
            return False

    async def get_by_user_id(self, user_id: str) -> Optional[dict]:
        if not self.surreal:
            return None

        try:
            result = await self.surreal._call('query',
                "SELECT * FROM voice_profile WHERE user_id = $user_id LIMIT 1;",
                {"user_id": user_id}
            )
            if result and isinstance(result, list) and len(result) > 0:
                data = result[0].get("result", [])
                if data and len(data) > 0:
                    return data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get voice profile: {e}")
            return None

    async def get_all_profiles(self) -> list[dict]:
        if not self.surreal:
            return []

        try:
            result = await self.surreal._call('query',
                "SELECT * FROM voice_profile WHERE is_active = true;"
            )
            if result and isinstance(result, list) and len(result) > 0:
                return result[0].get("result", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get all voice profiles: {e}")
            return []

    async def delete_profile(self, user_id: str) -> bool:
        if not self.surreal:
            return False

        try:
            await self.surreal._call('query',
                "DELETE FROM voice_profile WHERE user_id = $user_id;",
                {"user_id": user_id}
            )
            logger.info(f"Voice profile deleted for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete voice profile: {e}")
            return False

    async def deactivate_profile(self, user_id: str) -> bool:
        if not self.surreal:
            return False

        try:
            await self.surreal._call('query',
                "UPDATE voice_profile SET is_active = false WHERE user_id = $user_id;",
                {"user_id": user_id}
            )
            logger.info(f"Voice profile deactivated for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate voice profile: {e}")
            return False
