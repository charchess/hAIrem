from typing import Any, Dict, Optional
import os

class LlmClient:
    api_key: Any = None
    base_url: Any = None

    def __init__(self, cache: Any | None = None, config_override: Dict[str, Any] | None = None):
        config_override = config_override or {}
        self.model = config_override.get("model") or os.getenv("LLM_MODEL", "ollama/mistral")
        
        self.api_key = config_override.get("api_key") or os.getenv("LLM_API_KEY")
        self.base_url = config_override.get("base_url") or os.getenv("LLM_BASE_URL")
