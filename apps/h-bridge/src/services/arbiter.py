import logging
import re
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_AGENTS = [
    {
        "id": "chef",
        "name": "Chef",
        "type": "expert",
        "description": "Culinary expert agent",
        "domains": ["cooking", "recipes", "kitchen", "food", "dining"],
        "expertise": ["cooking", "recipes", "nutrition", "kitchen equipment"],
        "interests": ["cooking", "recipes", "food", "dining", "nutrition"],
        "personality_traits": ["helpful", "creative", "detail-oriented"],
        "supported_emotions": ["happy", "excited", "neutral"],
        "emotional_range": ["happy", "neutral"],
        "empathy_level": 0.6,
        "adaptability": 0.5,
        "is_active": True,
        "priority_weight": 1.0,
    },
    {
        "id": "tech",
        "name": "Tech",
        "type": "expert",
        "description": "Technical support agent",
        "domains": ["programming", "technology", "computers", "software", "coding"],
        "expertise": ["programming", "software", "computers", "troubleshooting"],
        "interests": ["programming", "technology", "coding", "computers"],
        "personality_traits": ["analytical", "patient", "logical"],
        "supported_emotions": ["neutral", "focused"],
        "emotional_range": ["neutral", "focused"],
        "empathy_level": 0.4,
        "adaptability": 0.6,
        "is_active": True,
        "priority_weight": 1.0,
    },
    {
        "id": "companion",
        "name": "Companion",
        "type": "companion",
        "description": "Emotional support and conversation agent",
        "domains": ["conversation", "emotional_support", "social", "company"],
        "expertise": ["conversation", "emotional_support", "active_listening"],
        "interests": ["conversation", "social", "emotional_support", "company"],
        "personality_traits": ["empathetic", "warm", "supportive", "understanding"],
        "supported_emotions": ["happy", "sad", "excited", "worried", "neutral", "angry"],
        "emotional_range": ["happy", "sad", "excited", "worried", "neutral", "angry", "frustrated"],
        "empathy_level": 0.9,
        "adaptability": 0.8,
        "is_active": True,
        "priority_weight": 1.0,
    },
    {
        "id": "gardener",
        "name": "Gardener",
        "type": "expert",
        "description": "Gardening and plant care agent",
        "domains": ["gardening", "plants", "outdoor", "nature"],
        "expertise": ["gardening", "plants", "landscaping", "plant care"],
        "interests": ["gardening", "plants", "nature", "outdoor"],
        "personality_traits": ["patient", "nurturing", "observant"],
        "supported_emotions": ["happy", "neutral", "excited"],
        "emotional_range": ["happy", "neutral", "excited"],
        "empathy_level": 0.5,
        "adaptability": 0.5,
        "is_active": True,
        "priority_weight": 1.0,
    },
]


class SimpleArbiter:
    def __init__(self):
        self._agents: dict[str, dict] = {}
        self._scores_cache: dict[str, list] = {}
        self.minimum_threshold = 0.2
        self.scoring_config = {
            "relevance_weight": 0.5,
            "interest_weight": 0.3,
            "emotional_weight": 0.2,
        }

    def register_agent(self, manifest: dict) -> None:
        self._agents[manifest["id"]] = manifest
        logger.info(f"Arbiter: Registered agent {manifest['id']}")

    def get_registered_agents(self) -> list[dict]:
        return list(self._agents.values())

    def _extract_keywords(self, text: str) -> list[str]:
        text = text.lower()
        keywords = re.findall(r"\b\w+\b", text)
        return list(set(keywords))

    def _calculate_interest_score(self, agent: dict, message: str) -> float:
        keywords = self._extract_keywords(message)
        score = 0.0

        for keyword in keywords:
            for interest in agent.get("interests", []):
                if keyword in interest.lower() or interest.lower() in keyword:
                    score += 0.3
            for domain in agent.get("domains", []):
                if keyword in domain.lower() or domain.lower() in keyword:
                    score += 0.2
            for expertise in agent.get("expertise", []):
                if keyword in expertise.lower() or expertise.lower() in keyword:
                    score += 0.25

        return min(score / max(len(keywords), 1), 1.0)

    def _detect_emotions(self, text: str) -> dict:
        text_lower = text.lower()

        emotion_keywords = {
            "happy": ["happy", "great", "wonderful", "excited", "love", "good", "amazing", "awesome", "joy"],
            "sad": ["sad", "unhappy", "depressed", "down", "unfortunate", "sorry", "miss", "lonely"],
            "angry": ["angry", "mad", "furious", "frustrated", "annoyed", "irritated", "hate"],
            "worried": ["worried", "anxious", "nervous", "concerned", "scared", "afraid", "fear"],
            "excited": ["excited", "thrilled", "eager", "can't wait", "looking forward"],
        }

        detected = []
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(emotion)
                    break

        intensity = min(len(detected) / 3, 1.0)

        return {
            "primary_emotion": detected[0] if detected else "neutral",
            "detected_emotions": detected,
            "overall_intensity": intensity,
            "sentiment_polarity": "positive"
            if any(e in ["happy", "excited"] for e in detected)
            else "negative"
            if any(e in ["sad", "angry", "worried"] for e in detected)
            else "neutral",
        }

    def _calculate_emotional_score(self, agent: dict, emotions: dict) -> float:
        primary_emotion = emotions.get("primary_emotion", "neutral")
        intensity = emotions.get("overall_intensity", 0.0)

        if primary_emotion == "neutral":
            return 0.5

        agent_emotions = agent.get("supported_emotions", [])
        if primary_emotion in agent_emotions:
            return 0.5 + (intensity * 0.5)

        return 0.1 * intensity

    def _detect_named_agent(self, message: str) -> str | None:
        message_lower = message.lower()

        for agent_id, agent in self._agents.items():
            name = agent.get("name", "").lower()
            if name in message_lower:
                return agent_id

            for interest in agent.get("interests", []):
                if interest.lower() in message_lower and len(interest) > 4:
                    return None

        return None

    def _score_agent(self, agent: dict, message: str) -> float:
        interest_score = self._calculate_interest_score(agent, message)
        emotions = self._detect_emotions(message)
        emotional_score = self._calculate_emotional_score(agent, emotions)

        relevance_score = interest_score

        final_score = (
            relevance_score * self.scoring_config["relevance_weight"]
            + interest_score * self.scoring_config["interest_weight"]
            + emotional_score * self.scoring_config["emotional_weight"]
        ) * agent.get("priority_weight", 1.0)

        return min(final_score, 1.0)

    def select_agent(self, message: str, context: dict | None = None) -> dict | None:
        context = context or {}
        mentioned_agents = context.get("mentioned_agents", [])

        if mentioned_agents:
            for agent_id in mentioned_agents:
                if agent_id in self._agents and self._agents[agent_id].get("is_active", True):
                    return {"agent_id": agent_id, **self._agents[agent_id]}

        named_agent = self._detect_named_agent(message)
        if named_agent and self._agents.get(named_agent, {}).get("is_active", True):
            return {"agent_id": named_agent, **self._agents[named_agent]}

        active_agents = [a for a in self._agents.values() if a.get("is_active", True)]

        if not active_agents:
            return None

        scored = []
        for agent in active_agents:
            score = self._score_agent(agent, message)
            scored.append((agent, score))

        scored.sort(key=lambda x: -x[1])

        if scored and scored[0][1] >= self.minimum_threshold:
            result = {"agent_id": scored[0][0]["id"], **scored[0][0]}
            result["score"] = scored[0][1]
            return result

        return None

    def score_agents(self, message: str, agent_ids: list[str] | None = None) -> list[tuple[dict, float]]:
        if agent_ids:
            agents = [self._agents[a] for a in agent_ids if a in self._agents]
        else:
            agents = [a for a in self._agents.values() if a.get("is_active", True)]

        scored = []
        for agent in agents:
            score = self._score_agent(agent, message)
            scored.append((agent, score))

        scored.sort(key=lambda x: -x[1])
        return scored


class ArbiterAPIService:
    def __init__(self, redis_client=None, surreal_client=None):
        self.redis = redis_client
        self.surreal = surreal_client
        self._arbiter = SimpleArbiter()
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        for manifest in DEFAULT_AGENTS:
            self._arbiter.register_agent(manifest)

        self._initialized = True
        logger.info("ArbiterAPIService: Initialized with default agents")

    async def select_agent(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        result = self._arbiter.select_agent(message, context)

        if result:
            return {
                "selected": True,
                "agent": {
                    "agent_id": result.get("agent_id"),
                    "name": result.get("name"),
                    "role": result.get("role"),
                },
                "message": "Agent selected successfully",
            }
        else:
            return {
                "selected": False,
                "agent": None,
                "message": "No suitable agent found for this message",
            }

    async def score_agents(
        self,
        message: str,
        agents: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        scored = self._arbiter.score_agents(message, agents)

        scored_agents = []
        for agent, score in scored:
            scored_agents.append(
                {
                    "agent_id": agent.get("id"),
                    "name": agent.get("name"),
                    "role": agent.get("role"),
                    "score": round(score, 4),
                    "interests": agent.get("interests", []),
                    "domains": agent.get("domains", []),
                    "expertise": agent.get("expertise", []),
                }
            )

        return {
            "message": message,
            "scores": scored_agents,
            "count": len(scored_agents),
        }

    def get_config(self) -> dict[str, Any]:
        if not self._initialized:
            return {
                "initialized": False,
                "message": "Service not yet initialized",
            }

        registered_agents = self._arbiter.get_registered_agents()

        return {
            "initialized": True,
            "minimum_threshold": self._arbiter.minimum_threshold,
            "suppression_enabled": True,
            "agents": [
                {
                    "agent_id": a.get("id"),
                    "name": a.get("name"),
                    "role": a.get("role"),
                    "is_active": a.get("is_active", True),
                    "interests": a.get("interests", []),
                    "domains": a.get("domains", []),
                    "expertise": a.get("expertise", []),
                    "priority_weight": a.get("priority_weight", 1.0),
                }
                for a in registered_agents
            ],
            "scoring_config": self._arbiter.scoring_config,
        }

    def get_topics(self, message: str) -> dict[str, Any]:
        if not self._initialized:
            return {"error": "Service not initialized"}

        keywords = self._arbiter._extract_keywords(message)
        return {
            "keywords": keywords,
            "topics": [],
            "message": message,
        }

    def get_emotions(self, message: str) -> dict[str, Any]:
        if not self._initialized:
            return {"error": "Service not initialized"}

        return self._arbiter._detect_emotions(message)

    def get_suppression_stats(self) -> dict[str, Any]:
        if not self._initialized:
            return {"error": "Service not initialized"}

        return {
            "suppressed_count": 0,
            "queue_size": 0,
        }

    async def add_agent_from_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        agent_id = manifest.get("id")
        if not agent_id:
            return {"success": False, "error": "id is required"}

        self._arbiter.register_agent(manifest)

        return {
            "success": True,
            "agent_id": agent_id,
            "message": f"Agent {manifest.get('name', agent_id)} registered successfully",
        }

    async def debug_scoring(self, message: str, context: dict = {}) -> dict:
        """
        Debug endpoint - returns scores for all agents without selection.
        """
        if not self._initialized:
            await self.initialize()

        scores = []
        agents = self._arbiter.score_agents(message, None)
        for agent, score in agents:
            scores.append(
                {
                    "agent_id": agent.get("id"),
                    "name": agent.get("name"),
                    "score": round(score, 4),
                    "interests": agent.get("interests", []),
                    "domains": agent.get("domains", []),
                }
            )

        return {
            "message": message,
            "scores": scores,
            "count": len(scores),
        }
