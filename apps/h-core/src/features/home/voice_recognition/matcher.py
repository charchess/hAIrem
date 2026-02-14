import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceMatcher:
    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold

    def compare_embeddings(
        self,
        embedding1: list[float],
        embedding2: list[float]
    ) -> float:
        if not embedding1 or not embedding2:
            return 0.0

        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            if vec1.shape != vec2.shape:
                min_len = min(len(vec1), len(vec2))
                vec1 = vec1[:min_len]
                vec2 = vec2[:min_len]

            cosine_sim = self._cosine_similarity(vec1, vec2)
            return float(cosine_sim)
        except Exception as e:
            logger.error(f"Failed to compare embeddings: {e}")
            return 0.0

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def find_best_match(
        self,
        query_embedding: list[float],
        stored_profiles: list[dict]
    ) -> tuple[Optional[dict], float]:
        if not query_embedding or not stored_profiles:
            return None, 0.0

        best_match = None
        best_score = 0.0

        for profile in stored_profiles:
            stored_embedding = profile.get("embedding", [])
            if not stored_embedding:
                continue

            similarity = self.compare_embeddings(query_embedding, stored_embedding)

            if similarity > best_score:
                best_score = similarity
                best_match = profile

        if best_score >= self.similarity_threshold:
            return best_match, best_score

        return None, best_score

    def is_match(self, similarity: float) -> bool:
        return similarity >= self.similarity_threshold
