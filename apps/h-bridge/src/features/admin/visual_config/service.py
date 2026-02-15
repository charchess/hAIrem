import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

SUPPORTED_VISUAL_PROVIDERS = {
    "nanobanana": {
        "name": "NanoBanana",
        "default_model": "sdxl",
        "default_base_url": os.getenv("NANOBANANA_BASE_URL", "http://localhost:8000"),
        "supports_reference_images": True,
        "supports_style_preset": True,
    },
    "google": {
        "name": "Google Imagen",
        "default_model": os.getenv("GOOGLE_IMAGEN_MODEL", "imagen-4.0-fast-generate-001"),
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "supports_reference_images": False,
        "supports_aspect_ratio": True,
    },
    "imagen-v2": {
        "name": "Imagen V2",
        "default_model": os.getenv("IMAGENV2_MODEL", "sdxl"),
        "default_base_url": os.getenv("IMAGENV2_BASE_URL", "http://localhost:8009"),
        "supports_reference_images": True,
        "supports_loras": True,
    },
}


def get_visual_provider_info(provider: str) -> dict[str, Any]:
    """Get visual provider information."""
    return SUPPORTED_VISUAL_PROVIDERS.get(provider.lower(), {
        "name": provider,
        "default_model": None,
        "default_base_url": None,
        "supports_reference_images": False,
        "supports_style_preset": False,
    })


def list_visual_providers() -> list[dict[str, Any]]:
    """List all supported visual providers."""
    return [
        {"id": k, "name": v["name"], "default_model": v["default_model"]}
        for k, v in SUPPORTED_VISUAL_PROVIDERS.items()
    ]


def is_valid_provider(provider: str) -> bool:
    """Check if provider is supported."""
    return provider.lower() in SUPPORTED_VISUAL_PROVIDERS


DEFAULT_VISUAL_CONFIG = {
    "provider": os.getenv("DEFAULT_VISUAL_PROVIDER", "nanobanana"),
    "fallback_enabled": True,
    "default_provider": "nanobanana",
    "fallback_provider": "google",
}


class VisualConfigService:
    def __init__(self, db_client=None):
        self.db = db_client
        self._config = DEFAULT_VISUAL_CONFIG.copy()
        self._agent_configs = {}

    async def get_config(self) -> dict[str, Any]:
        """Get current visual configuration."""
        return self._config.copy()

    async def update_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Update visual configuration."""
        if "provider" in config:
            provider = config["provider"]
            if not is_valid_provider(provider):
                return {
                    "success": False,
                    "errors": [{"field": "provider", "message": f"Unsupported visual provider: {provider}"}]
                }
            self._config["provider"] = provider.lower()

        if "fallback_enabled" in config:
            self._config["fallback_enabled"] = bool(config["fallback_enabled"])

        if "fallback_provider" in config:
            fallback = config["fallback_provider"]
            if not is_valid_provider(fallback):
                return {
                    "success": False,
                    "errors": [{"field": "fallback_provider", "message": f"Unsupported visual provider: {fallback}"}]
                }
            self._config["fallback_provider"] = fallback.lower()

        return {"success": True, "config": self._config.copy()}

    async def get_agent_provider(self, agent_id: str) -> Optional[str]:
        """Get provider for a specific agent."""
        return self._agent_configs.get(agent_id)

    async def set_agent_provider(self, agent_id: str, provider: str) -> dict[str, Any]:
        """Set provider for a specific agent."""
        if not is_valid_provider(provider):
            return {
                "success": False,
                "errors": [{"field": "provider", "message": f"Unsupported visual provider: {provider}"}]
            }
        
        self._agent_configs[agent_id] = provider.lower()
        return {"success": True, "agent_id": agent_id, "provider": provider.lower()}

    async def get_provider_for_agent(self, agent_id: str) -> str:
        """Get effective provider for an agent (agent-specific or default)."""
        agent_provider = await self.get_agent_provider(agent_id)
        return agent_provider or self._config.get("provider", "nanobanana")
