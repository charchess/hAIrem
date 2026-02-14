import logging
from typing import Any

from src.features.admin.agent_config.models import LLMProviderConfig, AgentParameters
from src.features.admin.provider_config.models import get_provider_info, list_providers, SUPPORTED_PROVIDERS

logger = logging.getLogger(__name__)


class ProviderConfigService:
    def __init__(self, agent_config_service):
        self.agent_config_service = agent_config_service

    async def list_providers(self) -> list[dict[str, Any]]:
        return list_providers()

    async def get_provider_info(self, provider: str) -> dict[str, Any]:
        return get_provider_info(provider)

    async def configure_provider(self, agent_id: str, provider: str, model: str | None = None, base_url: str | None = None, api_key: str | None = None) -> dict[str, Any]:
        if provider.lower() not in SUPPORTED_PROVIDERS:
            return {
                "success": False,
                "errors": [{"field": "provider", "message": f"Unsupported provider: {provider}"}]
            }

        provider_info = get_provider_info(provider)
        
        parameters = {}
        if model:
            parameters["model"] = model
        elif provider_info.get("default_model"):
            parameters["model"] = f"{provider}/{provider_info['default_model']}"
        
        if base_url:
            parameters["base_url"] = base_url
        elif provider_info.get("default_base_url"):
            parameters["base_url"] = provider_info["default_base_url"]
        
        if api_key:
            parameters["api_key"] = api_key
        
        parameters["provider"] = provider
        
        return await self.agent_config_service.save_config(agent_id, parameters)

    async def add_fallback_provider(self, agent_id: str, provider: str, model: str | None = None, base_url: str | None = None, api_key: str | None = None, priority: int = 0) -> dict[str, Any]:
        if provider.lower() not in SUPPORTED_PROVIDERS:
            return {
                "success": False,
                "errors": [{"field": "provider", "message": f"Unsupported provider: {provider}"}]
            }

        current_config = await self.agent_config_service.get_config(agent_id)
        params_dict = current_config.get("parameters", {})
        
        fallback_providers = params_dict.get("fallback_providers", [])
        
        provider_info = get_provider_info(provider)
        
        new_fallback = {
            "provider": provider,
            "model": model or f"{provider}/{provider_info.get('default_model', '')}",
            "base_url": base_url or provider_info.get("default_base_url"),
            "api_key": api_key,
            "priority": priority
        }
        
        fallback_providers.append(new_fallback)
        
        params_dict["fallback_providers"] = fallback_providers
        
        return await self.agent_config_service.save_config(agent_id, params_dict)

    async def remove_fallback_provider(self, agent_id: str, provider: str) -> dict[str, Any]:
        current_config = await self.agent_config_service.get_config(agent_id)
        params_dict = current_config.get("parameters", {})
        
        fallback_providers = params_dict.get("fallback_providers", [])
        fallback_providers = [fb for fb in fallback_providers if fb.get("provider") != provider]
        
        params_dict["fallback_providers"] = fallback_providers
        
        return await self.agent_config_service.save_config(agent_id, params_dict)
