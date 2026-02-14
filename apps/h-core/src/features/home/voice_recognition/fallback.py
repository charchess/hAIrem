import logging
from typing import Optional
from datetime import datetime

from .models import SessionUser, VoiceIdentificationResult

logger = logging.getLogger(__name__)


class VoiceRecognitionFallback:
    def __init__(self):
        self._session_users: dict[str, SessionUser] = {}

    def create_anonymous_session(self, session_id: str) -> SessionUser:
        session_user = SessionUser(
            session_id=session_id,
            user_id=None,
            identified_at=None,
            is_anonymous=True
        )
        self._session_users[session_id] = session_user
        logger.info(f"Created anonymous session: {session_id}")
        return session_user

    def assign_user_to_session(
        self,
        session_id: str,
        user_id: str,
        user_name: Optional[str] = None
    ) -> SessionUser:
        session_user = SessionUser(
            session_id=session_id,
            user_id=user_id,
            identified_at=datetime.utcnow(),
            is_anonymous=False
        )
        self._session_users[session_id] = session_user
        logger.info(f"Assigned user {user_id} to session: {session_id}")
        return session_user

    def get_session_user(self, session_id: str) -> Optional[SessionUser]:
        return self._session_users.get(session_id)

    def clear_session(self, session_id: str) -> bool:
        if session_id in self._session_users:
            del self._session_users[session_id]
            logger.info(f"Cleared session: {session_id}")
            return True
        return False

    def handle_unidentified_voice(
        self,
        session_id: str,
        identification_result: VoiceIdentificationResult
    ) -> SessionUser:
        existing = self.get_session_user(session_id)
        if existing and not existing.is_anonymous:
            return existing

        if identification_result.identified:
            return self.assign_user_to_session(
                session_id,
                identification_result.user_id,
                identification_result.user_name
            )

        return self.create_anonymous_session(session_id)

    def manual_identify(
        self,
        session_id: str,
        user_id: str,
        user_name: Optional[str] = None
    ) -> SessionUser:
        logger.info(f"Manual identification for session {session_id}: user={user_id}")
        return self.assign_user_to_session(session_id, user_id, user_name)
