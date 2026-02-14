
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

class AgentInstance(BaseModel):
    config: AgentConfig
    path: str
    is_active: bool = True
