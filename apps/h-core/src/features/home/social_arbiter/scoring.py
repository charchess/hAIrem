import re
from typing import Any
from .models import AgentProfile
from .topic_extraction import TopicExtractor, InterestScorer
from .emotion_detection import EmotionDetector, EmotionalContext


class ScoringEngine:
    def __init__(
        self,
        relevance_weight: float = 0.5,
        interest_weight: float = 0.3,
        emotional_weight: float = 0.2,
        tiebreaker_margin: float = 0.1,
    ):
        self.relevance_weight = relevance_weight
        self.interest_weight = interest_weight
        self.emotional_weight = emotional_weight
        self.tiebreaker_margin = tiebreaker_margin
        self.topic_extractor = TopicExtractor()
        self.interest_scorer = InterestScorer()
        self.emotion_detector = EmotionDetector()

    def score_agent(
        self,
        agent: AgentProfile,
        message_content: str,
        emotional_context: dict[str, Any] | None = None,
    ) -> float:
        relevance_score = self._calculate_relevance(agent, message_content)
        interest_score = self.interest_scorer.calculate_interest_score(agent, message_content)
        
        if emotional_context and emotional_context.get("detected_emotions"):
            detected = emotional_context
        else:
            detected = self.emotion_detector.detect_emotions(message_content)
        
        emotional_score = self._calculate_emotional_fit(agent, detected)
        
        total_score = (
            relevance_score * self.relevance_weight
            + interest_score * self.interest_weight
            + emotional_score * self.emotional_weight
        )
        
        return total_score * agent.priority_weight

    def _calculate_relevance(self, agent: AgentProfile, message: str) -> float:
        message_lower = message.lower()
        
        domain_matches = 0
        for domain in agent.domains:
            if domain.lower() in message_lower:
                domain_matches += 1
        
        expertise_matches = 0
        for expert in agent.expertise:
            if expert.lower() in message_lower:
                expertise_matches += 1
        
        if agent.domains:
            domain_score = min(domain_matches / len(agent.domains), 1.0)
        else:
            domain_score = 0.0
            
        if agent.expertise:
            expertise_score = min(expertise_matches / len(agent.expertise), 1.0)
        else:
            expertise_score = 0.0
        
        return (domain_score * 0.6) + (expertise_score * 0.4)

    def _calculate_interest_match(self, agent: AgentProfile, message: str) -> float:
        if not agent.interests:
            return 0.0
            
        message_lower = message.lower()
        matches = sum(1 for interest in agent.interests if interest.lower() in message_lower)
        
        return min(matches / len(agent.interests), 1.0)

    def _calculate_emotional_fit(
        self, agent: AgentProfile, emotional_context: dict[str, Any] | EmotionalContext | None
    ) -> float:
        if not emotional_context:
            return 0.5
        
        if isinstance(emotional_context, dict):
            if not emotional_context.get("primary_emotion") and not emotional_context.get("detected_emotions"):
                return 0.5
            primary_emotion = emotional_context.get("primary_emotion")
            intensity = emotional_context.get("overall_intensity", 0.5)
        else:
            primary_emotion = emotional_context.primary_emotion
            intensity = emotional_context.overall_intensity
        
        if not primary_emotion:
            return 0.5
        
        personality_match = 0.0
        agent_traits = [t.lower() for t in agent.personality_traits]
        
        capability_match = 0.0
        if agent.emotional_capabilities:
            supported = [e.lower() for e in agent.emotional_capabilities.supported_emotions]
            if primary_emotion.lower() in supported:
                capability_match = agent.emotional_capabilities.empathy_level
            
            emotional_range = [e.lower() for e in agent.emotional_capabilities.emotional_range]
            if primary_emotion.lower() in emotional_range:
                capability_match = max(capability_match, 0.8)
        
        matches = sum(1 for trait in agent_traits if trait.lower() == primary_emotion.lower())
        personality_match = min(matches / max(len(agent.personality_traits), 1), 1.0)
        
        base_score = (personality_match * 0.4 + capability_match * 0.6)
        
        if isinstance(emotional_context, dict):
            intensity = emotional_context.get("overall_intensity", 0.5)
        
        return min(base_score * (0.5 + intensity * 0.5), 1.0)

    def are_scores_tied(self, score1: float, score2: float) -> bool:
        return abs(score1 - score2) < self.tiebreaker_margin
