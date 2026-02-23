import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.features.admin.provider_config.models import get_provider_info, list_providers, SUPPORTED_PROVIDERS
from src.features.admin.provider_config.service import ProviderConfigService


class TestProviderModels:
    def test_get_provider_info_existing_provider(self):
        result = get_provider_info("openai")

        assert result["name"] == "OpenAI"
        assert result["default_model"] == "gpt-4"
        assert result["supports_streaming"] is True

    def test_get_provider_info_case_insensitive(self):
        result = get_provider_info("OLLAMA")

        assert result["name"] == "Ollama"
        assert result["default_model"] == "llama2"

    def test_get_provider_info_unknown_provider(self):
        result = get_provider_info("unknown_provider")

        assert result["name"] == "unknown_provider"
        assert result["default_model"] is None
        assert result["default_base_url"] is None

    def test_list_providers_returns_all(self):
        result = list_providers()

        assert len(result) == len(SUPPORTED_PROVIDERS)
        assert all("id" in p and "name" in p and "default_model" in p for p in result)

    def test_list_providers_contains_expected_providers(self):
        result = list_providers()
        provider_ids = [p["id"] for p in result]

        assert "openai" in provider_ids
        assert "anthropic" in provider_ids
        assert "ollama" in provider_ids
        assert "deepseek" in provider_ids


class TestProviderConfigService:
    @pytest.mark.asyncio
    async def test_list_providers_delegates_to_model(self):
        mock_agent_config_service = MagicMock()
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.list_providers()

        assert len(result) == len(SUPPORTED_PROVIDERS)

    @pytest.mark.asyncio
    async def test_get_provider_info_delegates_to_model(self):
        mock_agent_config_service = MagicMock()
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.get_provider_info("anthropic")

        assert result["name"] == "Anthropic"

    @pytest.mark.asyncio
    async def test_configure_provider_unsupported(self):
        mock_agent_config_service = MagicMock()
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.configure_provider("agent1", "unsupported_provider")

        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["field"] == "provider"

    @pytest.mark.asyncio
    async def test_configure_provider_with_defaults(self):
        mock_agent_config_service = MagicMock()
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.configure_provider("agent1", "ollama")

        assert result["success"] is True
        mock_agent_config_service.save_config.assert_called_once()
        call_args = mock_agent_config_service.save_config.call_args
        assert call_args[0][0] == "agent1"
        params = call_args[0][1]
        assert params["provider"] == "ollama"
        assert "model" in params
        assert "base_url" in params

    @pytest.mark.asyncio
    async def test_configure_provider_with_custom_model(self):
        mock_agent_config_service = MagicMock()
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.configure_provider("agent1", "openai", model="gpt-4-turbo")

        assert result["success"] is True
        call_args = mock_agent_config_service.save_config.call_args
        params = call_args[0][1]
        assert "gpt-4-turbo" in params["model"]

    @pytest.mark.asyncio
    async def test_configure_provider_with_custom_base_url(self):
        mock_agent_config_service = MagicMock()
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.configure_provider("agent1", "ollama", base_url="http://custom:11434")

        assert result["success"] is True
        call_args = mock_agent_config_service.save_config.call_args
        params = call_args[0][1]
        assert params["base_url"] == "http://custom:11434"

    @pytest.mark.asyncio
    async def test_configure_provider_with_api_key(self):
        mock_agent_config_service = MagicMock()
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.configure_provider("agent1", "openai", api_key="sk-test123")

        assert result["success"] is True
        call_args = mock_agent_config_service.save_config.call_args
        params = call_args[0][1]
        assert params["api_key"] == "sk-test123"


class TestFallbackProviders:
    @pytest.mark.asyncio
    async def test_add_fallback_provider_unsupported(self):
        mock_agent_config_service = MagicMock()
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.add_fallback_provider("agent1", "unsupported")

        assert result["success"] is False
        assert result["errors"][0]["field"] == "provider"

    @pytest.mark.asyncio
    async def test_add_fallback_provider_first(self):
        mock_agent_config_service = MagicMock()
        mock_agent_config_service.get_config = AsyncMock(return_value={"parameters": {}})
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.add_fallback_provider("agent1", "anthropic")

        assert result["success"] is True
        mock_agent_config_service.save_config.assert_called_once()
        call_args = mock_agent_config_service.save_config.call_args
        params = call_args[0][1]
        assert "fallback_providers" in params
        assert len(params["fallback_providers"]) == 1
        assert params["fallback_providers"][0]["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_add_fallback_provider_with_priority(self):
        mock_agent_config_service = MagicMock()
        mock_agent_config_service.get_config = AsyncMock(return_value={"parameters": {}})
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.add_fallback_provider("agent1", "deepseek", priority=10)

        assert result["success"] is True
        call_args = mock_agent_config_service.save_config.call_args
        params = call_args[0][1]
        assert params["fallback_providers"][0]["priority"] == 10

    @pytest.mark.asyncio
    async def test_add_fallback_provider_appends_to_existing(self):
        mock_agent_config_service = MagicMock()
        existing_fallbacks = [{"provider": "ollama", "model": "ollama/llama2", "priority": 0}]
        mock_agent_config_service.get_config = AsyncMock(
            return_value={"parameters": {"fallback_providers": existing_fallbacks}}
        )
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.add_fallback_provider("agent1", "anthropic")

        assert result["success"] is True
        call_args = mock_agent_config_service.save_config.call_args
        params = call_args[0][1]
        assert len(params["fallback_providers"]) == 2

    @pytest.mark.asyncio
    async def test_remove_fallback_provider(self):
        mock_agent_config_service = MagicMock()
        existing_fallbacks = [
            {"provider": "ollama", "model": "ollama/llama2"},
            {"provider": "anthropic", "model": "anthropic/claude-3"},
        ]
        mock_agent_config_service.get_config = AsyncMock(
            return_value={"parameters": {"fallback_providers": existing_fallbacks}}
        )
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.remove_fallback_provider("agent1", "ollama")

        assert result["success"] is True
        call_args = mock_agent_config_service.save_config.call_args
        params = call_args[0][1]
        assert len(params["fallback_providers"]) == 1
        assert params["fallback_providers"][0]["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_remove_fallback_provider_not_found(self):
        mock_agent_config_service = MagicMock()
        existing_fallbacks = [{"provider": "ollama", "model": "ollama/llama2"}]
        mock_agent_config_service.get_config = AsyncMock(
            return_value={"parameters": {"fallback_providers": existing_fallbacks}}
        )
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.remove_fallback_provider("agent1", "nonexistent")

        assert result["success"] is True
        call_args = mock_agent_config_service.save_config.call_args
        params = call_args[0][1]
        assert len(params["fallback_providers"]) == 1


class TestDynamicUpdates:
    @pytest.mark.asyncio
    async def test_configure_provider_creates_new_config(self):
        mock_agent_config_service = MagicMock()
        mock_agent_config_service.get_config = AsyncMock(return_value={"parameters": {"temperature": 0.5}})
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.configure_provider("agent1", "openai", model="gpt-4o")

        assert result["success"] is True
        call_args = mock_agent_config_service.save_config.call_args
        params = call_args[0][1]
        assert params["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_fallback_provider_preserves_other_params(self):
        mock_agent_config_service = MagicMock()
        mock_agent_config_service.get_config = AsyncMock(
            return_value={"parameters": {"temperature": 0.7, "max_tokens": 2000, "model": "existing-model"}}
        )
        mock_agent_config_service.save_config = AsyncMock(return_value={"success": True})
        service = ProviderConfigService(mock_agent_config_service)

        result = await service.add_fallback_provider("agent1", "deepseek")

        assert result["success"] is True
        call_args = mock_agent_config_service.save_config.call_args
        params = call_args[0][1]
        assert params["temperature"] == 0.7
        assert params["max_tokens"] == 2000
        assert "fallback_providers" in params


class TestConnectionTesting:
    @pytest.mark.asyncio
    async def test_test_connection_litellm_not_available(self):
        import src.features.admin.provider_config.service as svc_module

        original = svc_module.LITELLM_AVAILABLE
        svc_module.LITELLM_AVAILABLE = False
        try:
            service = ProviderConfigService(MagicMock())
            result = await service.test_connection("openai")
            assert result["success"] is False
            assert "LiteLLM" in result["message"]
            assert result["latency_ms"] is None
        finally:
            svc_module.LITELLM_AVAILABLE = original

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hello!"

        with (
            patch("src.features.admin.provider_config.service.LITELLM_AVAILABLE", True),
            patch("src.features.admin.provider_config.service.litellm") as mock_litellm,
        ):
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)
            service = ProviderConfigService(MagicMock())
            result = await service.test_connection("openai", model="openai/gpt-4", api_key="sk-test")

        assert result["success"] is True
        assert result["latency_ms"] is not None
        assert "Hello!" in result["preview"]

    @pytest.mark.asyncio
    async def test_test_connection_failure_returns_error(self):
        with (
            patch("src.features.admin.provider_config.service.LITELLM_AVAILABLE", True),
            patch("src.features.admin.provider_config.service.litellm") as mock_litellm,
        ):
            mock_litellm.acompletion = AsyncMock(side_effect=Exception("connection refused"))
            service = ProviderConfigService(MagicMock())
            result = await service.test_connection("openai", api_key="sk-test")

        assert result["success"] is False
        assert "connection refused" in result["message"]
        assert result["latency_ms"] is None

    @pytest.mark.asyncio
    async def test_test_connection_ollama_uses_localhost_default(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "pong"

        with (
            patch("src.features.admin.provider_config.service.LITELLM_AVAILABLE", True),
            patch("src.features.admin.provider_config.service.litellm") as mock_litellm,
        ):
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)
            service = ProviderConfigService(MagicMock())
            await service.test_connection("ollama")
            call_kwargs = mock_litellm.acompletion.call_args[1]
            assert call_kwargs.get("base_url") == "http://localhost:11434"

    @pytest.mark.asyncio
    async def test_test_connection_uses_default_model_when_none_provided(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "ok"

        with (
            patch("src.features.admin.provider_config.service.LITELLM_AVAILABLE", True),
            patch("src.features.admin.provider_config.service.litellm") as mock_litellm,
        ):
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)
            service = ProviderConfigService(MagicMock())
            await service.test_connection("openai", api_key="sk-x")
            call_kwargs = mock_litellm.acompletion.call_args[1]
            assert "gpt-4" in call_kwargs["model"]
