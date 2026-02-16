import logging
from typing import Any

from .arbiter import SocialArbiter
from .models import AgentProfile, AgentEmotionalCapabilities
from .repository import AgentRepository
from .emotion_detection import EmotionalContext
from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient

logger = logging.getLogger(__name__)


class ArbiterService:
    def __init__(
        self,
        redis_client: RedisClient | None = None,
        surreal_client: SurrealDbClient | None = None,
    ):
        self.redis = redis_client
        self.repository = AgentRepository(surreal_client)
        self.arbiter = SocialArbiter(
            minimum_threshold=0.2,
            default_agent_id=None,
        )

    async def initialize_from_manifests(self, manifests: list[dict[str, Any]]) -> None:
        for manifest in manifests:
            emotional_capabilities = AgentEmotionalCapabilities(
                supported_emotions=manifest.get("supported_emotions", []),
                emotional_range=manifest.get("emotional_range", []),
                empathy_level=manifest.get("empathy_level", 0.5),
                adaptability=manifest.get("adaptability", 0.5),
            )
            profile = AgentProfile(
                agent_id=manifest.get("id", ""),
                name=manifest.get("name", ""),
                role=manifest.get("type", "standard"),
                description=manifest.get("description"),
                domains=manifest.get("domains", []),
                expertise=manifest.get("expertise", []),
                interests=manifest.get("interests", []),
                personality_traits=manifest.get("personality_traits", []),
                emotional_capabilities=emotional_capabilities,
                is_active=manifest.get("is_active", True),
                priority_weight=manifest.get("priority_weight", 1.0),
            )
            self.arbiter.register_agent(profile)
            logger.info(f"Loaded agent manifest: {profile.agent_id}")

    async def initialize_from_database(self) -> None:
        agents = await self.repository.load_all_agents()
        for agent in agents:
            self.arbiter.register_agent(agent)
            logger.info(f"Loaded agent from DB: {agent.agent_id}")

    async def on_message_received(
        self,
        message_content: str,
        sender_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[AgentProfile] | None:
        emotional_context = metadata.get("emotional_context") if metadata else None
        mentioned = metadata.get("mentioned_agents", []) if metadata else []

        responders = self.arbiter.determine_responder(
            message_content=message_content,
            emotional_context=emotional_context,
            mentioned_agents=mentioned,
        )

        if responders:
            agent_ids = [r.agent_id for r in responders]
            logger.info(f"Arbiter selected {agent_ids} to respond")
            detected_emotion = self.arbiter.detect_emotions(message_content)
            if self.redis:
                await self.redis.publish_event(
                    "arbiter.decision",
                    {
                        "selected_agents": agent_ids,
                        "message_content": message_content,
                        "sender_id": sender_id,
                        "detected_emotion": detected_emotion.primary_emotion,
                        "emotional_intensity": detected_emotion.overall_intensity,
                    },
                )

        return responders

    async def select_agent(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        responders = await self.on_message_received(message, "user", context)
        if responders:
            return {
                "success": True,
                "agents": [{"id": r.agent_id, "name": r.name, "score": 1.0} for r in responders],  # Simplified
            }
        return {"success": False, "error": "No agent selected"}

    def get_rankings(self, message_content: str) -> list[tuple[AgentProfile, float]]:
        return self.arbiter.rank_agents(message_content)

    def extract_topics(self, message_content: str) -> dict[str, list[str]]:
        from .topic_extraction import TopicExtractor

        extractor = TopicExtractor()
        return {
            "keywords": extractor.extract_keywords(message_content),
            "topics": extractor.extract_topics(message_content),
            "bigrams": extractor.extract_ngrams(message_content, 2),
        }

    def detect_emotions(self, message_content: str) -> EmotionalContext:
        return self.arbiter.detect_emotions(message_content)

    def get_agent_emotional_state(self, agent_id: str) -> dict[str, Any] | None:
        return self.arbiter.get_agent_emotional_state(agent_id)

    def get_agent_emotional_history(self, agent_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self.arbiter.get_agent_emotional_history(agent_id, limit)

    def set_agent_status(self, agent_id: str, is_active: bool) -> None:
        self.arbiter.set_agent_active(agent_id, is_active)
