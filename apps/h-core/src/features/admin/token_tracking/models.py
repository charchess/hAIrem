from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class TokenUsage:
    agent_id: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "model": self.model,
            "provider": self.provider,
            "total_tokens": self.total_tokens,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenUsage":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()

        return cls(
            agent_id=data.get("agent_id", ""),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            model=data.get("model", ""),
            provider=data.get("provider", ""),
            timestamp=timestamp,
        )


@dataclass
class AgentCostSummary:
    agent_id: str
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    request_count: int = 0

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "request_count": self.request_count,
        }


@dataclass
class TimePeriodTrend:
    period: str
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    request_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "period": self.period,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": self.total_cost,
            "request_count": self.request_count,
        }
