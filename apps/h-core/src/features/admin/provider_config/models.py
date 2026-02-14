import logging
from typing import Any
from src.features.admin.agent_config.models import LLMProviderConfig

logger = logging.getLogger(__name__)


SUPPORTED_PROVIDERS = {
    "ollama": {
        "name": "Ollama",
        "default_model": "llama2",
        "default_base_url": "http://localhost:11434",
        "supports_streaming": True,
    },
    "openrouter": {
        "name": "OpenRouter",
        "default_model": "openrouter/google/gemini-pro",
        "default_base_url": "https://openrouter.ai/api/v1",
        "supports_streaming": True,
    },
    "openai": {
        "name": "OpenAI",
        "default_model": "gpt-4",
        "default_base_url": "https://api.openai.com/v1",
        "supports_streaming": True,
    },
    "anthropic": {
        "name": "Anthropic",
        "default_model": "claude-3-opus-20240229",
        "default_base_url": "https://api.anthropic.com",
        "supports_streaming": True,
    },
    "google": {
        "name": "Google Gemini",
        "default_model": "gemini-pro",
        "default_base_url": "https://generativelanguage.googleapis.com/v1",
        "supports_streaming": True,
    },
    "azure": {
        "name": "Azure OpenAI",
        "default_model": "gpt-4",
        "default_base_url": None,
        "supports_streaming": True,
    },
    "deepseek": {
        "name": "DeepSeek",
        "default_model": "deepseek-chat",
        "default_base_url": "https://api.deepseek.com/v1",
        "supports_streaming": True,
    },
    "mistral": {
        "name": "Mistral AI",
        "default_model": "mistral-medium",
        "default_base_url": "https://api.mistral.ai/v1",
        "supports_streaming": True,
    },
}


def get_provider_info(provider: str) -> dict[str, Any]:
    """Get provider information."""
    return SUPPORTED_PROVIDERS.get(provider.lower(), {
        "name": provider,
        "default_model": None,
        "default_base_url": None,
        "supports_streaming": True,
    })


def list_providers() -> list[dict[str, Any]]:
    """List all supported providers."""
    return [
        {"id": k, "name": v["name"], "default_model": v["default_model"]}
        for k, v in SUPPORTED_PROVIDERS.items()
    ]
