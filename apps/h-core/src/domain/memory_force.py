import math
from dataclasses import dataclass, field
from typing import Any, List, Optional


IMPORTANCE_HIGH_KEYWORDS = {
    "always",
    "never",
    "hate",
    "love",
    "promise",
    "important",
    "critical",
    "essential",
    "birthday",
    "anniversary",
    "death",
    "born",
    "married",
    "divorced",
    "favorite",
    "allergic",
    "medical",
    "phobia",
    "fear",
    "dream",
    "goal",
    "work",
    "family",
    "refuse",
    "obsessed",
    "passionate",
    "trauma",
    "secret",
}

IMPORTANCE_LOW_KEYWORDS = {
    "sometimes",
    "maybe",
    "perhaps",
    "usually",
    "often",
    "generally",
    "might",
    "could",
    "sort of",
    "kind of",
    "apparently",
}


@dataclass
class MemoryForce:
    affect: float = 0.5
    importance: float = 0.5
    relevance: float = 0.5

    @property
    def score(self) -> float:
        return min(1.0, self.affect * 0.30 + self.importance * 0.45 + self.relevance * 0.25)

    @property
    def decay_multiplier(self) -> float:
        return max(0.1, 1.0 - self.score * 0.9)

    def to_dict(self) -> dict[str, Any]:
        return {
            "force_score": round(self.score, 4),
            "affect": round(self.affect, 4),
            "importance": round(self.importance, 4),
            "relevance": round(self.relevance, 4),
        }


class MemoryForceEvaluator:
    def __init__(self) -> None:
        self._scope_embeddings: dict[str, List[float]] = {}

    def register_scopes(self, agent_id: str, scope_texts: List[str], embeddings: List[List[float]]) -> None:
        for text, emb in zip(scope_texts, embeddings):
            self._scope_embeddings[f"{agent_id}:{text}"] = emb

    def compute_affect(self, emotional_context: Optional[Any]) -> float:
        if not emotional_context:
            return 0.3
        raw_intensity = getattr(emotional_context, "overall_intensity", 0.0)
        polarity = getattr(emotional_context, "sentiment_polarity", 0.0)
        polarity_boost = abs(polarity) * 0.2
        return min(1.0, (raw_intensity / 1.5) + polarity_boost)

    def compute_importance(self, fact_text: str) -> float:
        text_lower = fact_text.lower()
        score = 0.3

        high_hits = sum(1 for kw in IMPORTANCE_HIGH_KEYWORDS if kw in text_lower)
        low_hits = sum(1 for kw in IMPORTANCE_LOW_KEYWORDS if kw in text_lower)

        score += min(0.6, high_hits * 0.15)
        score -= min(0.2, low_hits * 0.05)

        word_count = len(fact_text.split())
        if 5 <= word_count <= 20:
            score += 0.1

        return min(1.0, max(0.0, score))

    def compute_relevance(self, fact_embedding: List[float], agent_id: str) -> float:
        keys = [k for k in self._scope_embeddings if k.startswith(f"{agent_id}:")]
        if not keys or not fact_embedding:
            return 0.3

        max_sim = max(self._cosine_similarity(fact_embedding, self._scope_embeddings[k]) for k in keys)
        return max_sim

    def evaluate(
        self,
        fact_text: str,
        fact_embedding: List[float],
        agent_id: str,
        emotional_context: Optional[Any] = None,
    ) -> MemoryForce:
        return MemoryForce(
            affect=self.compute_affect(emotional_context),
            importance=self.compute_importance(fact_text),
            relevance=self.compute_relevance(fact_embedding, agent_id),
        )

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x**2 for x in a))
        norm_b = math.sqrt(sum(x**2 for x in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))
