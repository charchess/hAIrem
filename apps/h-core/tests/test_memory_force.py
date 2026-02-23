import math
import pytest
from unittest.mock import MagicMock

from src.domain.memory_force import (
    MemoryForce,
    MemoryForceEvaluator,
    IMPORTANCE_HIGH_KEYWORDS,
    IMPORTANCE_LOW_KEYWORDS,
)


class TestMemoryForce:
    def test_score_weighted_sum(self):
        f = MemoryForce(affect=1.0, importance=1.0, relevance=1.0)
        assert f.score == pytest.approx(1.0)

    def test_score_capped_at_one(self):
        f = MemoryForce(affect=2.0, importance=2.0, relevance=2.0)
        assert f.score <= 1.0

    def test_score_formula(self):
        f = MemoryForce(affect=0.6, importance=0.8, relevance=0.4)
        expected = min(1.0, 0.6 * 0.30 + 0.8 * 0.45 + 0.4 * 0.25)
        assert f.score == pytest.approx(expected, abs=1e-4)

    def test_decay_multiplier_low_force(self):
        f = MemoryForce(affect=0.0, importance=0.0, relevance=0.0)
        assert f.decay_multiplier == pytest.approx(1.0, abs=0.01)

    def test_decay_multiplier_high_force(self):
        f = MemoryForce(affect=1.0, importance=1.0, relevance=1.0)
        assert f.decay_multiplier == pytest.approx(0.1, abs=0.01)

    def test_decay_multiplier_never_below_0_1(self):
        f = MemoryForce(affect=100.0, importance=100.0, relevance=100.0)
        assert f.decay_multiplier >= 0.1

    def test_to_dict_keys(self):
        f = MemoryForce(affect=0.3, importance=0.7, relevance=0.5)
        d = f.to_dict()
        assert set(d.keys()) == {"force_score", "affect", "importance", "relevance"}
        assert d["force_score"] == pytest.approx(f.score, abs=1e-3)

    def test_to_dict_rounded(self):
        f = MemoryForce(affect=0.123456, importance=0.654321, relevance=0.111111)
        d = f.to_dict()
        assert len(str(d["affect"]).split(".")[-1]) <= 4


class TestMemoryForceEvaluatorAffect:
    def setup_method(self):
        self.evaluator = MemoryForceEvaluator()

    def test_affect_no_context(self):
        assert self.evaluator.compute_affect(None) == pytest.approx(0.3)

    def test_affect_neutral(self):
        ctx = MagicMock(overall_intensity=0.0, sentiment_polarity=0.0)
        assert self.evaluator.compute_affect(ctx) == pytest.approx(0.0, abs=0.01)

    def test_affect_high_intensity(self):
        ctx = MagicMock(overall_intensity=1.5, sentiment_polarity=0.0)
        assert self.evaluator.compute_affect(ctx) == pytest.approx(1.0)

    def test_affect_polarity_boost(self):
        ctx = MagicMock(overall_intensity=0.0, sentiment_polarity=-1.0)
        result = self.evaluator.compute_affect(ctx)
        assert result == pytest.approx(0.2, abs=0.01)

    def test_affect_capped_at_one(self):
        ctx = MagicMock(overall_intensity=99.0, sentiment_polarity=1.0)
        assert self.evaluator.compute_affect(ctx) <= 1.0


class TestMemoryForceEvaluatorImportance:
    def setup_method(self):
        self.evaluator = MemoryForceEvaluator()

    def test_importance_baseline(self):
        score = self.evaluator.compute_importance("the user said something")
        assert 0.0 <= score <= 1.0

    def test_importance_high_keyword(self):
        score = self.evaluator.compute_importance("User is allergic to peanuts")
        assert score > 0.4

    def test_importance_multiple_high_keywords(self):
        score = self.evaluator.compute_importance("User loves their family and has a dream to become a doctor")
        assert score > 0.5

    def test_importance_low_keywords_reduce_score(self):
        high = self.evaluator.compute_importance("User loves coffee")
        low = self.evaluator.compute_importance("User sometimes maybe loves coffee")
        assert low <= high

    def test_importance_word_count_bonus(self):
        short = self.evaluator.compute_importance("ok")
        medium = self.evaluator.compute_importance("user said they enjoy playing chess on weekends")
        assert medium >= short

    def test_importance_clamped(self):
        for kw in list(IMPORTANCE_HIGH_KEYWORDS)[:10]:
            score = self.evaluator.compute_importance(" ".join([kw] * 20))
            assert 0.0 <= score <= 1.0


class TestMemoryForceEvaluatorRelevance:
    def setup_method(self):
        self.evaluator = MemoryForceEvaluator()

    def test_relevance_no_scopes(self):
        emb = [0.1] * 4
        assert self.evaluator.compute_relevance(emb, "agent_x") == pytest.approx(0.3)

    def test_relevance_empty_embedding(self):
        self.evaluator.register_scopes("agent_x", ["topic"], [[0.1, 0.2, 0.3, 0.4]])
        assert self.evaluator.compute_relevance([], "agent_x") == pytest.approx(0.3)

    def test_relevance_perfect_match(self):
        emb = [1.0, 0.0, 0.0, 0.0]
        self.evaluator.register_scopes("agent_y", ["topic"], [[1.0, 0.0, 0.0, 0.0]])
        result = self.evaluator.compute_relevance(emb, "agent_y")
        assert result == pytest.approx(1.0, abs=0.01)

    def test_relevance_orthogonal(self):
        emb = [1.0, 0.0]
        self.evaluator.register_scopes("agent_z", ["topic"], [[0.0, 1.0]])
        result = self.evaluator.compute_relevance(emb, "agent_z")
        assert result == pytest.approx(0.0, abs=0.01)

    def test_relevance_uses_max_across_scopes(self):
        emb = [1.0, 0.0, 0.0]
        self.evaluator.register_scopes(
            "agent_m",
            ["scope_a", "scope_b"],
            [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0]],
        )
        result = self.evaluator.compute_relevance(emb, "agent_m")
        assert result == pytest.approx(1.0, abs=0.01)


class TestMemoryForceEvaluatorCosine:
    def test_identical_vectors(self):
        v = [0.3, 0.4, 0.5]
        assert MemoryForceEvaluator._cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-5)

    def test_orthogonal(self):
        assert MemoryForceEvaluator._cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_zero_vector(self):
        assert MemoryForceEvaluator._cosine_similarity([0.0, 0.0], [1.0, 1.0]) == pytest.approx(0.0)

    def test_mismatched_lengths(self):
        assert MemoryForceEvaluator._cosine_similarity([1.0, 2.0], [1.0]) == pytest.approx(0.0)

    def test_empty_vectors(self):
        assert MemoryForceEvaluator._cosine_similarity([], []) == pytest.approx(0.0)

    def test_negative_components(self):
        result = MemoryForceEvaluator._cosine_similarity([-1.0, 0.0], [1.0, 0.0])
        assert result == pytest.approx(0.0)


class TestMemoryForceEvaluatorEvaluate:
    def setup_method(self):
        self.evaluator = MemoryForceEvaluator()

    def test_evaluate_returns_memory_force(self):
        emb = [0.1] * 10
        result = self.evaluator.evaluate("User loves coffee", emb, "agent1")
        assert isinstance(result, MemoryForce)

    def test_evaluate_with_emotional_context(self):
        ctx = MagicMock(overall_intensity=1.0, sentiment_polarity=0.5)
        emb = [0.1] * 10
        result = self.evaluator.evaluate("User is afraid of spiders", emb, "agent1", ctx)
        assert result.affect > 0.5

    def test_evaluate_no_context_default_affect(self):
        emb = [0.1] * 10
        result = self.evaluator.evaluate("User said hello", emb, "agent1", None)
        assert result.affect == pytest.approx(0.3)
