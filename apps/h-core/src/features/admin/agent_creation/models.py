from pydantic import BaseModel, Field, field_validator
from typing import Any


class AgentCreationPayload(BaseModel):
    name: str = Field(..., min_length=1, description="Unique agent identifier")
    role: str = Field(..., min_length=1, description="Agent role/persona")
    description: str | None = Field(default=None, description="Agent description")
    prompt: str | None = Field(default=None, description="System prompt")
    model: str | None = Field(default=None, description="LLM model to use")
    temperature: float | None = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=2048, ge=1, le=8192)
    top_p: float | None = Field(default=0.9, ge=0.0, le=1.0)
    base_url: str | None = Field(default=None, description="LLM API base URL")
    api_key: str | None = Field(default=None, description="LLM API key")
    enabled: bool = True
    agents_folder: str | None = Field(default=None, description="Path to agent folder (for hotplug)")

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str | None) -> str | None:
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v

    def to_agent_config(self) -> dict[str, Any]:
        config = {
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "prompt": self.prompt,
            "capabilities": [],
            "personified": True,
            "use_default_tools": True,
        }
        
        llm_config = {}
        if self.model:
            llm_config["model"] = self.model
        if self.temperature is not None:
            llm_config["temperature"] = self.temperature
        if self.max_tokens is not None:
            llm_config["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            llm_config["top_p"] = self.top_p
        if self.base_url:
            llm_config["base_url"] = self.base_url
        if self.api_key:
            llm_config["api_key"] = self.api_key
            
        if llm_config:
            config["llm_config"] = llm_config
            
        return config

    def to_manifest_dict(self) -> dict[str, Any]:
        return {
            "id": self.name,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "version": "1.0.0",
            "system_prompt": self.prompt,
            "llm_config": {
                "model": self.model or "ollama/mistral",
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "base_url": self.base_url,
                "api_key": self.api_key,
            } if any([self.model, self.temperature, self.max_tokens, self.top_p, self.base_url, self.api_key]) else None,
            "enabled": self.enabled,
        }
