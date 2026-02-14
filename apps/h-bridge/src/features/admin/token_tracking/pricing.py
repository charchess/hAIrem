from dataclasses import dataclass
from typing import Dict


@dataclass
class ProviderPricing:
    provider: str
    model: str
    input_cost_per_1m: float
    output_cost_per_1m: float

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_1m
        return input_cost + output_cost


PROVIDER_PRICING: Dict[str, ProviderPricing] = {
    "openai:gpt-4": ProviderPricing(
        provider="openai",
        model="gpt-4",
        input_cost_per_1m=30.0,
        output_cost_per_1m=60.0,
    ),
    "openai:gpt-4-turbo": ProviderPricing(
        provider="openai",
        model="gpt-4-turbo",
        input_cost_per_1m=10.0,
        output_cost_per_1m=30.0,
    ),
    "openai:gpt-3.5-turbo": ProviderPricing(
        provider="openai",
        model="gpt-3.5-turbo",
        input_cost_per_1m=0.5,
        output_cost_per_1m=1.5,
    ),
    "anthropic:claude-3-opus": ProviderPricing(
        provider="anthropic",
        model="claude-3-opus",
        input_cost_per_1m=15.0,
        output_cost_per_1m=75.0,
    ),
    "anthropic:claude-3-sonnet": ProviderPricing(
        provider="anthropic",
        model="claude-3-sonnet",
        input_cost_per_1m=3.0,
        output_cost_per_1m=15.0,
    ),
    "anthropic:claude-3-haiku": ProviderPricing(
        provider="anthropic",
        model="claude-3-haiku",
        input_cost_per_1m=0.25,
        output_cost_per_1m=1.25,
    ),
    "google:gemini-pro": ProviderPricing(
        provider="google",
        model="gemini-pro",
        input_cost_per_1m=1.25,
        output_cost_per_1m=5.0,
    ),
    "default": ProviderPricing(
        provider="unknown",
        model="unknown",
        input_cost_per_1m=1.0,
        output_cost_per_1m=3.0,
    ),
}


def get_pricing(provider: str, model: str) -> ProviderPricing:
    key = f"{provider}:{model}"
    return PROVIDER_PRICING.get(key, PROVIDER_PRICING["default"])


def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = get_pricing(provider, model)
    return pricing.calculate_cost(input_tokens, output_tokens)
