from typing import List, Optional
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    name: str
    role: str
    description: Optional[str] = None
    version: str = "1.0.0"
    capabilities: List[str] = Field(default_factory=list)
    prompt: Optional[str] = None
    visual_id: Optional[str] = None

class AgentInstance(BaseModel):
    config: AgentConfig
    path: str
    is_active: bool = True
