import logging
from typing import Any

from src.features.admin.agent_config.models import AgentConfigSchema, AgentParameters, DEFAULT_PARAMETERS
from src.features.admin.agent_config.repository import AgentConfigRepository

logger = logging.getLogger(__name__)


class ValidationError:
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "message": self.message}


class AgentConfigService:
    def __init__(self, surreal_client, agent_registry=None):
        self.repository = AgentConfigRepository(surreal_client)
        self.agent_registry = agent_registry
        self._config_cache: dict[str, AgentParameters] = {}

    async def initialize(self):
        logger.info("AgentConfigService: Initializing...")
        await self._load_all_configs()

    async def _load_all_configs(self):
        configs = await self.repository.list_all()
        for config in configs:
            self._config_cache[config.agent_id] = config.parameters
        logger.info(f"AgentConfigService: Loaded {len(self._config_cache)} configurations")

    def validate_parameters(self, parameters: dict[str, Any]) -> list[ValidationError]:
        errors = []
        
        if "temperature" in parameters and parameters["temperature"] is not None:
            if not (0.0 <= parameters["temperature"] <= 2.0):
                errors.append(ValidationError("temperature", "Must be between 0.0 and 2.0"))
        
        if "max_tokens" in parameters and parameters["max_tokens"] is not None:
            if not (1 <= parameters["max_tokens"] <= 8192):
                errors.append(ValidationError("max_tokens", "Must be between 1 and 8192"))
        
        if "top_p" in parameters and parameters["top_p"] is not None:
            if not (0.0 <= parameters["top_p"] <= 1.0):
                errors.append(ValidationError("top_p", "Must be between 0.0 and 1.0"))
        
        if "top_k" in parameters and parameters["top_k"] is not None:
            if parameters["top_k"] < 1:
                errors.append(ValidationError("top_k", "Must be at least 1"))
        
        if "presence_penalty" in parameters and parameters["presence_penalty"] is not None:
            if not (-2.0 <= parameters["presence_penalty"] <= 2.0):
                errors.append(ValidationError("presence_penalty", "Must be between -2.0 and 2.0"))
        
        if "frequency_penalty" in parameters and parameters["frequency_penalty"] is not None:
            if not (-2.0 <= parameters["frequency_penalty"] <= 2.0):
                errors.append(ValidationError("frequency_penalty", "Must be between -2.0 and 2.0"))
        
        if "context_window" in parameters and parameters["context_window"] is not None:
            if not (1024 <= parameters["context_window"] <= 128000):
                errors.append(ValidationError("context_window", "Must be between 1024 and 128000"))
        
        if "base_url" in parameters and parameters["base_url"]:
            if not (parameters["base_url"].startswith("http://") or parameters["base_url"].startswith("https://")):
                errors.append(ValidationError("base_url", "Must start with http:// or https://"))
        
        if "model" in parameters and parameters["model"]:
            if not parameters["model"].strip():
                errors.append(ValidationError("model", "Cannot be empty"))
        
        return errors

    async def save_config(self, agent_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if not agent_id or not agent_id.strip():
            return {"success": False, "errors": [{"field": "agent_id", "message": "Agent ID is required"}]}

        errors = self.validate_parameters(parameters)
        if errors:
            return {"success": False, "errors": [e.to_dict() for e in errors]}

        try:
            params = AgentParameters.from_dict(parameters)
            await self.repository.save(agent_id, params)
            self._config_cache[agent_id] = params
            
            await self._apply_config_to_agent(agent_id, params)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "parameters": params.to_dict()
            }
        except Exception as e:
            logger.error(f"AgentConfigService: Failed to save config for {agent_id}: {e}")
            return {"success": False, "errors": [{"field": "general", "message": str(e)}]}

    async def get_config(self, agent_id: str) -> dict[str, Any]:
        if agent_id in self._config_cache:
            params = self._config_cache[agent_id]
        else:
            params = await self.repository.get_or_default(agent_id)
            self._config_cache[agent_id] = params
        
        return {
            "success": True,
            "agent_id": agent_id,
            "parameters": params.to_dict()
        }

    async def list_configs(self) -> dict[str, Any]:
        configs = await self.repository.list_all()
        return {
            "success": True,
            "configs": [
                {
                    "agent_id": c.agent_id,
                    "parameters": c.parameters.to_dict(),
                    "enabled": c.enabled,
                    "version": c.version
                }
                for c in configs
            ]
        }

    async def delete_config(self, agent_id: str) -> dict[str, Any]:
        result = await self.repository.delete(agent_id)
        if result and agent_id in self._config_cache:
            del self._config_cache[agent_id]
        
        return {
            "success": result,
            "agent_id": agent_id
        }

    async def _apply_config_to_agent(self, agent_id: str, parameters: AgentParameters):
        """Apply config to agent with proper priority.
        
        Priority: DB Override > YAML Manifest > Env Vars
        
        Only apply non-None values from DB to avoid overriding manifest config.
        """
        if not self.agent_registry or agent_id not in self.agent_registry.agents:
            logger.warning(f"AgentConfigService: Agent {agent_id} not found in registry, config saved but not applied")
            return

        agent = self.agent_registry.agents[agent_id]
        
        if hasattr(agent, "llm_client") and agent.llm_client:
            llm = agent.llm_client
            
            # Only override with explicit DB values (non-None)
            # This preserves YAML manifest and env var fallbacks
            if parameters.temperature is not None:
                llm.temperature = parameters.temperature
            if parameters.model is not None and parameters.model.strip():
                llm.model = parameters.model
                logger.info(f"AgentConfigService: Overriding model for {agent_id} to {parameters.model}")
            if parameters.base_url is not None and parameters.base_url.strip():
                llm.base_url = parameters.base_url
                logger.info(f"AgentConfigService: Overriding base_url for {agent_id}")
            if parameters.api_key is not None and parameters.api_key.strip():
                llm.api_key = parameters.api_key
            
            if parameters.fallback_providers:
                fallback_configs = [
                    {
                        "model": fb.model or parameters.model,
                        "api_key": fb.api_key,
                        "base_url": fb.base_url,
                        "priority": fb.priority
                    }
                    for fb in parameters.fallback_providers
                ]
                llm.update_fallback_providers(fallback_configs)
        
        if hasattr(agent, "config") and agent.config:
            if parameters.system_prompt is not None:
                agent.config.prompt = parameters.system_prompt
        
        logger.info(f"AgentConfigService: Applied config to agent {agent_id}")

    def get_effective_parameters(self, agent_id: str) -> AgentParameters:
        if agent_id in self._config_cache:
            return self._config_cache[agent_id]
        return DEFAULT_PARAMETERS
