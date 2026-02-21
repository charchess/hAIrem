import pytest
from src.features.home.social_arbiter.scoring import ScoringEngine
from src.models.agent import AgentConfig

# TDD: Epic 3 - Social Arbiter Logic
# These tests cover the granular scoring logic that drives the arbiter decisions.


class TestScoringEngineLogic:
    def test_calculate_relevance_keyword_match(self):
        # FR19: Interest Scoring
        engine = ScoringEngine()
        text = "Tell me about quantum physics"
        # Agent has relevant domain
        score = engine.calculate_relevance(text, ["physics", "science"], "teacher")
        assert score > 0.5

    def test_calculate_relevance_no_match(self):
        engine = ScoringEngine()
        text = "What is for dinner?"
        score = engine.calculate_relevance(text, ["physics"], "teacher")
        assert score < 0.3

    def test_calculate_emotional_fit(self):
        # FR20: Emotional Context
        engine = ScoringEngine()
        # Happy text should match "cheerful" role/personality better than "grumpy"
        # This assumes we pass emotion analysis results
        text_emotion = "joy"

        score_cheerful = engine.calculate_emotional_fit(text_emotion, "cheerful_helper")
        score_grumpy = engine.calculate_emotional_fit(text_emotion, "grumpy_guard")

        assert score_cheerful > score_grumpy

    def test_score_decay_repetition(self):
        # FR23: Suppression/Repetition
        engine = ScoringEngine()
        base_score = 0.8

        # If agent just spoke, score should be penalized
        time_since_last_spoke = 5  # seconds
        adjusted_score = engine.apply_repetition_penalty(base_score, time_since_last_spoke)

        assert adjusted_score < base_score

        # If agent spoke long ago, penalty should be minimal
        time_since_last_spoke_long = 600
        adjusted_score_long = engine.apply_repetition_penalty(base_score, time_since_last_spoke_long)

        assert adjusted_score_long > adjusted_score

    def test_multi_agent_competition(self):
        # FR18: Agent Selection
        engine = ScoringEngine()
        input_text = "I need help with my python code"

        # Agent A: Coder
        score_a = engine.compute_total_score(
            text=input_text, domains=["coding", "python"], role="developer", time_since_spoke=100
        )

        # Agent B: Chef
        score_b = engine.compute_total_score(
            text=input_text, domains=["cooking", "food"], role="chef", time_since_spoke=100
        )

        assert score_a > score_b
