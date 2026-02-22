from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_ONBOARDED_KEY = "hairem:onboarded:{user_id}"
_SESSION_KEY = "hairem:onboarding:session:{user_id}"
_SESSION_TTL = 3600

INTERVIEW_QUESTIONS = [
    {
        "key": "preferred_name",
        "text": "Comment tu aimes qu'on t'appelle ?",
    },
    {
        "key": "interests",
        "text": "Qu'est-ce qui t'intéresse ? (musique, jeux, cuisine, tech…)",
    },
    {
        "key": "mood_today",
        "text": "Comment tu te sens aujourd'hui ?",
    },
    {
        "key": "household",
        "text": "Tu es seul·e à la maison, ou il y a d'autres personnes ?",
    },
]


class OnboardingService:
    def __init__(self, redis_client: Any, surreal_client: Any = None):
        self.redis = redis_client
        self.surreal = surreal_client

    async def is_onboarded(self, user_id: str) -> bool:
        try:
            client = self.redis.client
            if client is None:
                return True
            result = await client.get(_ONBOARDED_KEY.format(user_id=user_id))
            return result is not None
        except Exception:
            return True

    async def start_interview(self, user_id: str, user_name: str | None = None) -> dict[str, Any]:
        if await self.is_onboarded(user_id):
            return {"status": "already_onboarded", "user_id": user_id}

        session = {
            "user_id": user_id,
            "user_name": user_name or user_id,
            "step": 0,
            "answers": {},
        }
        await self._save_session(user_id, session)
        logger.info(f"ONBOARDING: Started interview for {user_id}")

        return {
            "status": "started",
            "user_id": user_id,
            "question": INTERVIEW_QUESTIONS[0]["text"],
            "step": 0,
            "total_steps": len(INTERVIEW_QUESTIONS),
        }

    async def submit_answer(self, user_id: str, answer: str) -> dict[str, Any]:
        session = await self._load_session(user_id)
        if not session:
            return await self.start_interview(user_id)

        step = session["step"]
        if step < len(INTERVIEW_QUESTIONS):
            question = INTERVIEW_QUESTIONS[step]
            session["answers"][question["key"]] = answer
            session["step"] = step + 1
            await self._save_session(user_id, session)

        if session["step"] >= len(INTERVIEW_QUESTIONS):
            return await self._complete_interview(user_id, session)

        next_question = INTERVIEW_QUESTIONS[session["step"]]
        return {
            "status": "in_progress",
            "step": session["step"],
            "total_steps": len(INTERVIEW_QUESTIONS),
            "question": next_question["text"],
        }

    async def _complete_interview(self, user_id: str, session: dict) -> dict[str, Any]:
        answers = session["answers"]

        await self._seed_memories(user_id, answers)
        await self._mark_onboarded(user_id)
        await self._delete_session(user_id)

        logger.info(f"ONBOARDING: Completed for {user_id} — answers: {answers}")

        try:
            await self.redis.publish_event(
                "system_stream",
                {
                    "type": "system.onboarding_complete",
                    "sender": {"agent_id": "core", "role": "system"},
                    "payload": {
                        "content": {
                            "user_id": user_id,
                            "user_name": session.get("user_name"),
                            "answers": answers,
                        }
                    },
                },
            )
        except Exception as e:
            logger.warning(f"ONBOARDING: Failed to broadcast completion — {e}")

        return {
            "status": "complete",
            "user_id": user_id,
            "answers": answers,
        }

    async def _seed_memories(self, user_id: str, answers: dict) -> None:
        if not self.surreal or not self.surreal.client:
            return
        try:
            facts = []
            if answers.get("preferred_name"):
                facts.append(f"L'utilisateur préfère être appelé·e '{answers['preferred_name']}'.")
            if answers.get("interests"):
                facts.append(f"Ses intérêts : {answers['interests']}.")
            if answers.get("mood_today"):
                facts.append(f"Humeur lors de l'onboarding : {answers['mood_today']}.")
            if answers.get("household"):
                facts.append(f"Contexte familial : {answers['household']}.")

            for fact in facts:
                await self.surreal._call(
                    "query",
                    f"CREATE fact SET content = '{fact}', user_id = '{user_id}', "
                    f"source = 'onboarding', created_at = time::now();",
                )
        except Exception as e:
            logger.warning(f"ONBOARDING: Failed to seed memories for {user_id} — {e}")

    async def _mark_onboarded(self, user_id: str) -> None:
        try:
            client = self.redis.client
            if client:
                await client.set(_ONBOARDED_KEY.format(user_id=user_id), "1")
        except Exception as e:
            logger.warning(f"ONBOARDING: Failed to mark onboarded — {e}")

    async def _save_session(self, user_id: str, session: dict) -> None:
        try:
            client = self.redis.client
            if client:
                await client.set(
                    _SESSION_KEY.format(user_id=user_id),
                    json.dumps(session),
                    ex=_SESSION_TTL,
                )
        except Exception as e:
            logger.warning(f"ONBOARDING: Failed to save session — {e}")

    async def _load_session(self, user_id: str) -> dict | None:
        try:
            client = self.redis.client
            if client is None:
                return None
            raw = await client.get(_SESSION_KEY.format(user_id=user_id))
            return json.loads(raw) if raw else None
        except Exception:
            return None

    async def _delete_session(self, user_id: str) -> None:
        try:
            client = self.redis.client
            if client:
                await client.delete(_SESSION_KEY.format(user_id=user_id))
        except Exception:
            pass
