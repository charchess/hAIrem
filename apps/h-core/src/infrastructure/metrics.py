from __future__ import annotations
from typing import Any

from prometheus_client import CollectorRegistry, Histogram, REGISTRY


class MetricsCollector:
    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        reg = registry or REGISTRY
        self._surreal = Histogram(
            "surrealdb_call_duration_seconds",
            "SurrealDB call latency",
            ["method"],
            registry=reg,
        )
        self._llm = Histogram(
            "llm_completion_duration_seconds",
            "LLM completion latency",
            ["model"],
            registry=reg,
        )
        self._tts = Histogram(
            "tts_synthesis_duration_seconds",
            "TTS synthesis latency",
            registry=reg,
        )

    def record_surrealdb_call(self, method: str, duration: float) -> None:
        self._surreal.labels(method=method).observe(duration)

    def record_llm_completion(self, model: str, duration: float) -> None:
        self._llm.labels(model=model).observe(duration)

    def record_tts_synthesis(self, duration: float) -> None:
        self._tts.observe(duration)


_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
