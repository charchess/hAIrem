import logging
import os
import time
from typing import Any

from src.features.admin.agent_config.models import LLMProviderConfig, AgentParameters
from src.features.admin.provider_config.models import get_provider_info, list_providers, SUPPORTED_PROVIDERS

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

logger = logging.getLogger(__name__)


class ProviderConfigService:
    def __init__(self, agent_config_service):
        self.agent_config_service = agent_config_service

    async def list_providers(self) -> list[dict[str, Any]]:
        return list_providers()

    async def get_provider_info(self, provider: str) -> dict[str, Any]:
        return get_provider_info(provider)

    async def test_connection(self, provider: str, model: str | None = None, base_url: str | None = None, api_key: str | None = None) -> dict[str, Any]:
        """Test LLM connectivity with given parameters.
        
        Returns:
            success: bool - Whether connection was successful
            message: str - Human-readable message
            latency_ms: int - Response time in milliseconds
        """
        if not LITELLM_AVAILABLE:
            return {
                "success": False,
                "message": "LiteLLM is not available. Please install it.",
                "latency_ms": None
            }
        
        try:
            provider_info = get_provider_info(provider)
            
            # Build the model string
            model_str = model
            if not model_str:
                if provider_info.get("default_model"):
                    model_str = f"{provider}/{provider_info['default_model']}"
                else:
                    model_str = provider
            
            # Build kwargs
            kwargs = {
                "model": model_str,
                "messages": [{"role": "user", "content": "Hi"}],
                "mock": False
            }
            
            if api_key:
                kwargs["api_key"] = api_key
            elif provider in ["openai", "anthropic", "google"]:
                # Try env var
                env_key = f"{provider.upper()}_API_KEY"
                env_val = os.getenv(env_key)
                if env_val:
                    kwargs["api_key"] = env_val
            
            if base_url:
                kwargs["base_url"] = base_url
            elif provider_info.get("default_base_url"):
                kwargs["base_url"] = provider_info["default_base_url"]
            
            # Special handling for Ollama
            if provider == "ollama" and not base_url:
                kwargs["base_url"] = "http://localhost:11434"
            
            # Test the connection
            start = time.time()
            response = await litellm.acompletion(**kwargs)
            latency_ms = int((time.time() - start) * 1000)
            
            content = response.choices[0].message.content
            logger.info(f"LLM test success: provider={provider}, model={model_str}, latency={latency_ms}ms")
            
            return {
                "success": True,
                "message": f"Connection successful! Model responded in {latency_ms}ms.",
                "latency_ms": latency_ms,
                "model": model_str,
                "preview": content[:100] if content else "No content"
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"LLM test failed: provider={provider}, error={error_msg}")
            return {
                "success": False,
                "message": f"Connection failed: {error_msg}",
                "latency_ms": None,
                "model": model
            }

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
