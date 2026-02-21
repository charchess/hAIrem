import logging
from typing import Any

from .models import AgentProfile
from .scoring import ScoringEngine
from .tiebreaker import Tiebreaker
from .fallback import FallbackBehavior
from .emotion_detection import EmotionDetector, EmotionalStateManager, EmotionalContext
from .name_detection import NameExtractor
from .suppression import (
    ResponseSuppressor,
    SuppressionConfig,
    SuppressionReason,
    SuppressedResponse,
)

logger = logging.getLogger(__name__)


class SocialArbiter:
    def __init__(
        self,
        minimum_threshold: float = 0.2,
        default_agent_id: str | None = None,
        scoring_config: dict[str, float] | None = None,
        suppression_config: dict[str, Any] | None = None,
        llm_client: Any | None = None,
    ):
        scoring_config = scoring_config or {}
        self.scoring_engine = ScoringEngine(
            relevance_weight=scoring_config.get("relevance_weight", 0.5),
            interest_weight=scoring_config.get("interest_weight", 0.3),
            emotional_weight=scoring_config.get("emotional_weight", 0.2),
            tiebreaker_margin=scoring_config.get("tiebreaker_margin", 0.1),
            llm_client=llm_client,
        )
        self.tiebreaker = Tiebreaker()
        self.fallback = FallbackBehavior(
            minimum_threshold=minimum_threshold,
            default_agent_id=default_agent_id,
        )

        supp_config = suppression_config or {}
        self.suppressor = ResponseSuppressor(
            SuppressionConfig(
                minimum_threshold=supp_config.get("minimum_threshold", 0.15),
                enable_suppression=supp_config.get("enable_suppression", True),
                enable_reevaluation=supp_config.get("enable_reevaluation", True),
                reevaluation_delay_seconds=supp_config.get("reevaluation_delay_seconds", 30.0),
                max_reevaluation_attempts=supp_config.get("max_reevaluation_attempts", 3),
            )
        )

        self._agents: dict[str, AgentProfile] = {}
        self.emotion_detector = EmotionDetector()
        self.emotion_state_manager = EmotionalStateManager()
        self.name_extractor = NameExtractor()

    def register_agent(self, agent: AgentProfile) -> None:
        self._agents[agent.agent_id] = agent
        logger.info(f"Social Arbiter: Registered agent {agent.agent_id}")

    def unregister_agent(self, agent_id: str) -> None:
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Social Arbiter: Unregistered agent {agent_id}")

    def get_registered_agents(self) -> list[AgentProfile]:
        return list(self._agents.values())

    def determine_responder(
        self,
        message_content: str,
        emotional_context: dict[str, Any] | None = None,
        mentioned_agents: list[str] | None = None,
        allow_suppression: bool = True,
    ) -> list[AgentProfile] | None:
        """Determines which agents should respond. Synchronous version."""
        # This is a wrapper around determined_responder_async for legacy compatibility
        # In a real async environment, use determine_responder_async
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We are in an async loop, but this is a sync call
                # Fallback to rule-based scoring to avoid blocking
                return self._determine_responder_sync(
                    message_content, emotional_context, mentioned_agents, allow_suppression
                )
            else:
                return loop.run_until_complete(
                    self.determine_responder_async(
                        message_content, emotional_context, mentioned_agents, allow_suppression
                    )
                )
        except RuntimeError:
            return self._determine_responder_sync(
                message_content, emotional_context, mentioned_agents, allow_suppression
            )

    async def determine_responder_async(
        self,
        message_content: str,
        emotional_context: dict[str, Any] | None = None,
        mentioned_agents: list[str] | None = None,
        allow_suppression: bool = True,
    ) -> list[AgentProfile] | None:
        """Determines which agents should respond using LLM scoring (ADR-10)."""
        mentioned_agents = mentioned_agents or []

        # 1. Detect mentions (Priority 1)
        if mentioned_agents:
            return [a for a in self._agents.values() if a.agent_id in mentioned_agents]

        active_agents = [a for a in self._agents.values() if a.is_active]
        if not active_agents:
            return None

        # 2. Collective greeting or general address? (Priority 2)
        greetings = ["bonjour", "salut", "hey", "coucou", "hello"]
        collective_terms = ["les filles", "tout le monde", "equipe", "l'equipe", "crew"]
        lower_content = message_content.lower()

        has_greeting = any(g in lower_content for g in greetings)
        has_collective = any(c in lower_content for c in collective_terms)

        if has_greeting and has_collective:
            logger.info("Social Arbiter: Collective greeting detected. Picking a spokesperson.")
            # Pick one random active agent to respond for the group
            import random

            return [random.choice(active_agents)]

        # 3. Named agent check (Priority 3)
        named_agent_id = self._detect_named_agent(message_content, active_agents)
        if named_agent_id:
            named_agent = self._agents.get(named_agent_id)
            if named_agent:
                return [named_agent]

        # 4. LLM-Based Scoring (Priority 4)
        # Pass emotional context to LLM
        detected_emotion = None
        if not emotional_context or not emotional_context.get("detected_emotions"):
            detected = self.emotion_detector.detect_emotions(message_content)
            if detected.primary_emotion:
                detected_emotion = {
                    "primary_emotion": detected.primary_emotion,
                    "overall_intensity": detected.overall_intensity,
                }
        else:
            detected_emotion = emotional_context

        llm_scores = await self.scoring_engine.calculate_relevance_llm(message_content, active_agents, detected_emotion)

        scored_agents = []
        for agent in active_agents:
            # Combine LLM relevance with Repetition Penalty
            relevance = llm_scores.get(agent.agent_id, 0.5)
            time_since = self.suppressor.get_time_since_last_spoke(agent.agent_id)
            final_score = self.scoring_engine.apply_repetition_penalty(relevance, time_since)
            scored_agents.append((agent, final_score))

        scored_agents.sort(key=lambda x: -x[1])

        # Cascade mode (> 0.75) - Story 18.2
        winners = [agent for agent, score in scored_agents if score > 0.75]
        if not winners and scored_agents:
            # Fallback to the single best if none are above cascade threshold
            # but only if it's not totally irrelevant (< 0.2)
            if scored_agents[0][1] > self.suppressor.config.minimum_threshold:
                winners = [scored_agents[0][0]]

        # Filter suppressed agents (ADR-10)
        if allow_suppression:
            filtered_list = []
            for agent in winners:
                # Find score for this agent
                score = next(s for a, s in scored_agents if a == agent)
                if not self.suppressor.should_suppress(agent.agent_id, score):
                    filtered_list.append(agent)
                else:
                    self.suppressor.suppress_response(
                        agent_id=agent.agent_id,
                        message_content=message_content,
                        score=score,
                        reason=SuppressionReason.LOW_RELEVANCE_SCORE,
                    )
            winners = filtered_list

        # Update emotional state for selected agents
        if winners and detected_emotion:
            for agent in winners:
                self.emotion_state_manager.update_emotional_state(
                    agent.agent_id,
                    detected_emotion.get("primary_emotion"),
                )

        return winners if winners else None

    def _determine_responder_sync(
        self,
        message_content: str,
        emotional_context: dict[str, Any] | None = None,
        mentioned_agents: list[str] | None = None,
        allow_suppression: bool = True,
    ) -> list[AgentProfile] | None:
        # Original rule-based implementation (moved here)
        mentioned_agents = mentioned_agents or []

        detected_emotion = None
        if not emotional_context or not emotional_context.get("detected_emotions"):
            detected = self.emotion_detector.detect_emotions(message_content)
            if detected.primary_emotion:
                detected_emotion = {
                    "primary_emotion": detected.primary_emotion,
                    "detected_emotions": [e.emotion for e in detected.detected_emotions],
                    "overall_intensity": detected.overall_intensity,
                    "sentiment_polarity": detected.sentiment_polarity,
                }
        else:
            detected_emotion = emotional_context

        if mentioned_agents:
            mentioned = [a for a in self._agents.values() if a.agent_id in mentioned_agents]
            if mentioned:
                if detected_emotion:
                    for agent in mentioned:
                        self.emotion_state_manager.update_emotional_state(
                            agent.agent_id,
                            detected_emotion.get("primary_emotion"),
                        )
                return mentioned

        active_agents = [a for a in self._agents.values() if a.is_active]
        if not active_agents:
            logger.warning("Social Arbiter: No active agents available")
            return None

        named_agent_id = self._detect_named_agent(message_content, active_agents)

        if named_agent_id:
            named_agent = self._agents.get(named_agent_id)
            if named_agent:
                logger.info(f"Social Arbiter: Named agent detected: {named_agent.name}")
                if detected_emotion:
                    self.emotion_state_manager.update_emotional_state(
                        named_agent.agent_id,
                        detected_emotion.get("primary_emotion"),
                    )
                return [named_agent]

        scored_agents = []
        for agent in active_agents:
            score = self.scoring_engine.score_agent(agent, message_content, detected_emotion)
            scored_agents.append((agent, score))

        scored_agents.sort(key=lambda x: -x[1])

        # Check for cascade: agents with score > 0.75
        cascade_agents = [agent for agent, score in scored_agents if score > 0.75]
        if cascade_agents:
            selected_list = cascade_agents
            logger.info(f"Social Arbiter: Cascade activation for {len(selected_list)} agents with score > 0.75")
        else:
            # No cascade, use tiebreaker if needed
            if len(scored_agents) > 1:
                top_score = scored_agents[0][1]
                second_score = scored_agents[1][1]
                if self.scoring_engine.are_scores_tied(top_score, second_score):
                    scored_agents = self.tiebreaker.apply(scored_agents)

            selected = self.fallback.select_agent(scored_agents, active_agents)
            selected_list = [selected] if selected else []

        # Filter suppressed agents
        if allow_suppression:
            filtered_list = []
            for agent in selected_list:
                agent_score = next(score for a, score in scored_agents if a == agent)
                if not self.suppressor.should_suppress(agent.agent_id, agent_score):
                    filtered_list.append(agent)
                else:
                    self.suppressor.suppress_response(
                        agent_id=agent.agent_id,
                        message_content=message_content,
                        score=agent_score,
                        reason=SuppressionReason.BELOW_THRESHOLD,
                        metadata={
                            "context": {
                                "emotional_context": detected_emotion,
                                "mentioned_agents": mentioned_agents,
                            }
                        },
                    )
                    logger.info(
                        f"Social Arbiter: Response suppressed for agent {agent.agent_id} "
                        f"(score: {agent_score:.3f} < threshold: {self.suppressor.config.minimum_threshold})"
                    )
            selected_list = filtered_list

        if not selected_list:
            return None

        # Update emotional state for selected agents
        if detected_emotion:
            for agent in selected_list:
                self.emotion_state_manager.update_emotional_state(
                    agent.agent_id,
                    detected_emotion.get("primary_emotion"),
                )

        return selected_list

    def _detect_named_agent(
        self,
        message_content: str,
        active_agents: list[AgentProfile],
    ) -> str | None:
        extracted_name = self.name_extractor.extract_name_from_message(message_content)

        if not extracted_name:
            return None

        agents_dict = {a.agent_id: a for a in active_agents}
        agent_id, is_exact_match = self.name_extractor.find_agent_by_name(
            extracted_name,
            agents_dict,
        )

        if agent_id:
            return agent_id

        logger.warning(f"Social Arbiter: Named agent '{extracted_name}' not found in system")
        return None

    def rank_agents(
        self,
        message_content: str,
        emotional_context: dict[str, Any] | None = None,
    ) -> list[tuple[AgentProfile, float]]:
        detected_emotion = None
        if not emotional_context or not emotional_context.get("detected_emotions"):
            detected = self.emotion_detector.detect_emotions(message_content)
            if detected.primary_emotion:
                detected_emotion = {
                    "primary_emotion": detected.primary_emotion,
                    "detected_emotions": [e.emotion for e in detected.detected_emotions],
                    "overall_intensity": detected.overall_intensity,
                    "sentiment_polarity": detected.sentiment_polarity,
                }
        else:
            detected_emotion = emotional_context

        active_agents = [a for a in self._agents.values() if a.is_active]

        scored_agents = []
        for agent in active_agents:
            score = self.scoring_engine.score_agent(agent, message_content, detected_emotion)
            scored_agents.append((agent, score))

        scored_agents.sort(key=lambda x: -x[1])

        return scored_agents

    def detect_emotions(self, message_content: str) -> EmotionalContext:
        return self.emotion_detector.detect_emotions(message_content)

    def get_agent_emotional_state(self, agent_id: str) -> dict[str, Any] | None:
        return self.emotion_state_manager.get_state(agent_id)

    def get_agent_emotional_history(self, agent_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self.emotion_state_manager.get_history(agent_id, limit)

    def update_agent_stats(self, agent_id: str, response_time: float) -> None:
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            agent.response_count += 1
            agent.last_response_time = response_time

    def set_agent_active(self, agent_id: str, is_active: bool) -> None:
        if agent_id in self._agents:
            self._agents[agent_id].is_active = is_active
            logger.info(f"Social Arbiter: Agent {agent_id} set to active={is_active}")

    def get_suppression_stats(self) -> dict[str, Any]:
        return self.suppressor.get_stats()

    def get_suppression_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.suppressor.suppression_logger.get_suppression_history(limit)

    def process_pending_reevaluations(
        self,
        message_content: str,
        current_context: dict[str, Any] | None = None,
    ) -> list[SuppressedResponse]:
        current_context = current_context or {}
        pending = self.suppressor.get_pending_reevaluations()
        reevaluated = []

        for suppressed in pending:
            context_change_score = self.suppressor.check_context_change(suppressed, current_context)

            new_score = suppressed.score + context_change_score

            if new_score >= self.suppressor.config.minimum_threshold:
                agent = self._agents.get(suppressed.agent_id)
                if agent:
                    logger.info(
                        f"Social Arbiter: Re-evaluating suppressed response for {suppressed.agent_id}, "
                        f"new score: {new_score:.3f} (original: {suppressed.score:.3f}, "
                        f"context change: {context_change_score:.3f})"
                    )
                    reevaluated.append(suppressed)

        return reevaluated

    def get_pending_reevaluation_count(self) -> int:
        return self.suppressor.get_queue_size()

    def clear_suppression_queue(self) -> int:
        return self.suppressor.clear_queue()

    def set_suppression_threshold(self, threshold: float) -> None:
        self.suppressor.config.minimum_threshold = threshold
        logger.info(f"Social Arbiter: Suppression threshold set to {threshold}")

    def enable_suppression(self, enabled: bool) -> None:
        self.suppressor.config.enable_suppression = enabled
        logger.info(f"Social Arbiter: Suppression {'enabled' if enabled else 'disabled'}")
