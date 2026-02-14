from pydantic import BaseModel, Field, field_validator
from typing import Any


class LLMProviderConfig(BaseModel):
    provider: str = Field(default="ollama", description="LLM provider name (e.g., ollama, openai, anthropic)")
    model: str | None = Field(default=None, description="Model identifier")
    base_url: str | None = Field(default=None, description="LLM API base URL")
    api_key: str | None = Field(default=None, description="LLM API key")
    priority: int = Field(default=0, description="Provider priority (lower = higher priority)")

    @field_validator("api_key")
    @classmethod
    def mask_api_key(cls, v: str | None) -> str | None:
        if v and len(v) > 4:
            return v[:4] + "*" * (len(v) - 4)
        return v

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str | None) -> str | None:
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMProviderConfig":
        if not data:
            return cls()
        return cls.model_validate(data)


class AgentParameters(BaseModel):
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Controls randomness in generation (0.0-2.0)")
    max_tokens: int | None = Field(default=None, ge=1, le=8192, description="Maximum tokens to generate")
    top_p: float | None = Field(default=None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: int | None = Field(default=None, ge=1, description="Top-k sampling parameter")
    presence_penalty: float | None = Field(default=None, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: float | None = Field(default=None, ge=-2.0, le=2.0, description="Frequency penalty")
    repeat_penalty: float | None = Field(default=None, ge=0.0, le=2.0, description="Repeat penalty")
    model: str | None = Field(default=None, min_length=1, description="Model identifier")
    base_url: str | None = Field(default=None, description="LLM API base URL")
    api_key: str | None = Field(default=None, description="LLM API key")
    system_prompt: str | None = Field(default=None, description="System prompt/persona")
    context_window: int | None = Field(default=None, ge=1024, le=128000, description="Context window size")
    stop: list[str] | None = Field(default=None, description="Stop sequences")
    provider: str | None = Field(default=None, description="LLM provider (e.g., ollama, openai, anthropic)")
    fallback_providers: list[LLMProviderConfig] = Field(default_factory=list, description="Fallback providers list")

    @field_validator("api_key")
    @classmethod
    def mask_api_key(cls, v: str | None) -> str | None:
        if v and len(v) > 4:
            return v[:4] + "*" * (len(v) - 4)
        return v

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str | None) -> str | None:
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentParameters":
        if not data:
            return cls()
        return cls.model_validate(data)


class AgentConfigSchema(BaseModel):
    agent_id: str = Field(..., min_length=1)
    parameters: AgentParameters = Field(default_factory=AgentParameters)
    enabled: bool = True
    version: str = "1.0.0"


DEFAULT_PARAMETERS = AgentParameters(
    temperature=0.7,
    max_tokens=2048,
    top_p=0.9,
    model="ollama/mistral"
)
