from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

_GLOBAL_METRICS: "MetricsCollector | None" = None


class MetricsCollector:
    def __init__(self) -> None:
        self._counters: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)

    def increment(self, name: str, value: float = 1) -> None:
        self._counters[name] += value

    def get(self, name: str) -> float:
        return self._counters.get(name, 0)

    def observe(self, name: str, value: float) -> None:
        self._histograms[name].append(value)

    def get_avg(self, name: str) -> float:
        values = self._histograms.get(name, [])
        if not values:
            return 0.0
        return sum(values) / len(values)

    def to_prometheus_text(self) -> str:
        lines: List[str] = []
        for name, value in self._counters.items():
            int_val = int(value) if value == int(value) else value
            lines.append(f"{name} {int_val}")
        for name, values in self._histograms.items():
            if values:
                avg = sum(values) / len(values)
                lines.append(f"{name}_avg {avg}")
                lines.append(f"{name}_count {len(values)}")
        return "\n".join(lines)


def get_metrics() -> MetricsCollector:
    global _GLOBAL_METRICS
    if _GLOBAL_METRICS is None:
        _GLOBAL_METRICS = MetricsCollector()
    return _GLOBAL_METRICS
