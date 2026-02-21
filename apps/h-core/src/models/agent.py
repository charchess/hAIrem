from typing import Optional
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    name: str
    role: str
    description: str | None = None
    version: str = "1.0.0"
    capabilities: list[str] = Field(default_factory=list)
    prompt: str | None = None
    visual_id: str | None = None
    llm_config: dict | None = None
    personified: bool = True
    use_default_tools: bool = True
    room_id: str | None = Field(default=None, description="Room assignment identifier")
    skills: list[dict] = Field(default_factory=list, description="List of dynamic skills defined in persona")
    theme_responses: dict[str, dict] = Field(default_factory=dict, description="Custom reactions to world themes")
    preferred_location: str | None = Field(default=None, description="Preferred room identifier")
    voice_id: Optional[str] = None


class AgentInstance(BaseModel):
    config: AgentConfig
    path: str
    is_active: bool = True
