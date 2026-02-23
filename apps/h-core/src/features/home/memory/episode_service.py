import logging
from datetime import datetime
from typing import Any

from src.features.home.memory.episode import Episode
from src.infrastructure.llm import LlmClient
from src.infrastructure.surrealdb import SurrealDbClient

logger = logging.getLogger(__name__)

_SUMMARY_PROMPT = """
Summarize this conversation episode in 2-3 sentences, focusing on key facts learned and the emotional arc.

Facts extracted:
{facts}

Emotion arc:
{emotion_arc}

Output: a concise plain-text summary (no JSON, no bullet points).
"""


class EpisodeService:
    def __init__(self, surreal: SurrealDbClient, llm: LlmClient) -> None:
        self.surreal = surreal
        self.llm = llm

    async def open_episode(self, session_id: str, agent_id: str, user_id: str | None = None) -> Episode:
        episode_id = await self.surreal.open_episode(session_id, agent_id, user_id)
        return Episode(
            episode_id=episode_id,
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
        )

    async def close_episode(
        self,
        session_id: str,
        emotion_records: list[dict[str, Any]] | None = None,
    ) -> Episode:
        emotion_arc = emotion_records or []
        facts = await self.surreal.get_episode_facts(session_id)
        summary = await self._generate_summary(facts, emotion_arc)
        await self.surreal.close_episode(session_id, summary, emotion_arc)

        raw = await self.surreal.get_episode(session_id)
        episode_id = str(raw.get("id", "")) if raw else ""
        ended_at_raw = raw.get("ended_at") if raw else None
        ended_at: datetime | None = None
        if ended_at_raw:
            try:
                ended_at = datetime.fromisoformat(str(ended_at_raw).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                ended_at = datetime.utcnow()

        return Episode(
            episode_id=episode_id,
            session_id=session_id,
            agent_id=raw.get("agent_id", "") if raw else "",
            user_id=raw.get("user_id") if raw else None,
            ended_at=ended_at,
            summary=summary,
            emotion_arc=emotion_arc,
            fact_ids=[f.get("id", "") for f in facts],
        )

    async def _generate_summary(self, facts: list[dict[str, Any]], emotion_arc: list[dict[str, Any]]) -> str:
        if not facts:
            return ""
        facts_text = "\n".join(f"- {f.get('content', '')}" for f in facts)
        arc_text = ", ".join(e.get("emotion", "") for e in emotion_arc) if emotion_arc else "neutral"
        prompt = _SUMMARY_PROMPT.format(facts=facts_text, emotion_arc=arc_text)
        try:
            response = await self.llm.get_completion([{"role": "system", "content": prompt}], stream=False)
            return str(response).strip() if isinstance(response, str) else ""
        except Exception as exc:
            logger.warning(f"Episode summary generation failed: {exc}")
            return ""

    async def get_episode_context(self, session_id: str) -> dict[str, Any]:
        raw = await self.surreal.get_episode(session_id)
        if not raw:
            return {}
        facts = await self.surreal.get_episode_facts(session_id)
        return {
            "session_id": session_id,
            "summary": raw.get("summary"),
            "emotion_arc": raw.get("emotion_arc", []),
            "facts": [f.get("content", "") for f in facts],
        }

    async def get_temporal_context(self, agent_id: str, since_days: int = 7) -> list[Episode]:
        raw_episodes = await self.surreal.get_recent_episodes(agent_id, limit=50)
        episodes: list[Episode] = []
        for raw in raw_episodes:
            ended_at_raw = raw.get("ended_at")
            ended_at: datetime | None = None
            if ended_at_raw:
                try:
                    ended_at = datetime.fromisoformat(str(ended_at_raw).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            started_at_raw = raw.get("started_at")
            started_at = datetime.utcnow()
            if started_at_raw:
                try:
                    started_at = datetime.fromisoformat(str(started_at_raw).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            age_days = (datetime.utcnow() - started_at.replace(tzinfo=None)).days
            if age_days > since_days:
                continue

            episodes.append(
                Episode(
                    episode_id=str(raw.get("id", "")),
                    session_id=raw.get("session_id", ""),
                    agent_id=raw.get("agent_id", ""),
                    user_id=raw.get("user_id"),
                    started_at=started_at.replace(tzinfo=None),
                    ended_at=ended_at.replace(tzinfo=None) if ended_at else None,
                    summary=raw.get("summary"),
                    emotion_arc=raw.get("emotion_arc", []),
                )
            )
        return episodes
