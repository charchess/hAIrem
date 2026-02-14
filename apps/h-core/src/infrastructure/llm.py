import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

try:
    import litellm
    from litellm import acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    litellm = None  # type: ignore
    acompletion = None
    LITELLM_AVAILABLE = False
    print("WARNING: litellm library not found. LLM features will be disabled.")

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False
    print("WARNING: fastembed library not found. Local embeddings will be disabled.")

logger = logging.getLogger(__name__)

if LITELLM_AVAILABLE:
    litellm.drop_params = True
    litellm.success_callback = [] 
    litellm.failure_callback = []


class LlmClient:
    api_key: Any = None
    base_url: Any = None
    embedding_model = None
    _fallback_providers: list[dict[str, Any]] = []
    _fallback_index: int = 0
    _current_provider: dict[str, Any] | None = None

    def __init__(self, cache: Any | None = None, config_override: dict[str, Any] | None = None, fallback_providers: list[dict[str, Any]] | None = None):
        config_override = config_override or {}
        self.model = config_override.get("model") or os.getenv("LLM_MODEL", "ollama/mistral")
        
        raw_key = config_override.get("api_key") or os.getenv("LLM_API_KEY")
        self.api_key = str(raw_key) if raw_key else None
        self.base_url = config_override.get("base_url") or os.getenv("LLM_BASE_URL")
        
        self.temperature = config_override.get("temperature")
        self.cache = cache
        
        self._fallback_providers = fallback_providers or []
        self._fallback_index = 0
        self._current_provider = {
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.base_url
        }
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            os.environ["OPENROUTER_API_KEY"] = openrouter_key
            logger.info(f"OpenRouter API Key detected. Using Model: {self.model}")
        
        if FASTEMBED_AVAILABLE:
            try:
                self.embedding_model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
                logger.info("FastEmbed initialized with model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 dim)")
            except Exception as e:
                logger.error(f"Failed to initialize FastEmbed: {e}")
        else:
            logger.warning("FastEmbed not available. Embeddings will fail.")
        
        logger.info(f"Initializing LlmClient with Model: {self.model}, Fallback Providers: {len(self._fallback_providers)}")

    def update_fallback_providers(self, providers: list[dict[str, Any]]):
        """Update fallback providers list dynamically."""
        self._fallback_providers = sorted(providers, key=lambda x: x.get("priority", 0))
        self._fallback_index = 0
        logger.info(f"Updated fallback providers: {len(self._fallback_providers)} providers")

    def _get_current_provider_config(self) -> dict[str, Any]:
        """Get the current provider configuration."""
        return self._current_provider or {
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.base_url
        }

    def _get_next_fallback(self) -> dict[str, Any] | None:
        """Get the next fallback provider configuration."""
        if not self._fallback_providers or self._fallback_index >= len(self._fallback_providers):
            return None
        
        fallback = self._fallback_providers[self._fallback_index]
        self._fallback_index += 1
        return {
            "model": fallback.get("model") or self.model,
            "api_key": fallback.get("api_key") or self.api_key,
            "base_url": fallback.get("base_url") or self.base_url
        }

    def _reset_fallback_index(self):
        """Reset the fallback index for a new request."""
        self._fallback_index = 0

    async def get_completion(self, messages: list[dict[str, str]], stream: bool = False, tools: list[dict[str, Any]] | None = None, return_full_object: bool = False) -> str | AsyncGenerator[str, None] | Any:
        """
        Get completion from the LLM using litellm with automatic fallback.
        """
        if not LITELLM_AVAILABLE:
            err_msg = "Mon cerveau (LLM) n'est pas encore branché."
            return self._error_generator(err_msg) if stream else err_msg

        self._reset_fallback_index()
        
        provider_config = self._get_current_provider_config()
        
        while True:
            try:
                kwargs = {
                    "model": provider_config["model"],
                    "messages": messages,
                    "stream": stream
                }
                
                if provider_config.get("api_key"):
                    kwargs["api_key"] = provider_config["api_key"]
                if provider_config.get("base_url"):
                    kwargs["base_url"] = provider_config["base_url"]
                if self.temperature is not None:
                    kwargs["temperature"] = float(self.temperature)

                if tools:
                    kwargs["tools"] = tools

                logger.info(f"LLM_CALL: Model={provider_config['model']}, Tools={len(tools) if tools else 0}, FallbackIndex={self._fallback_index}")
                response = await asyncio.wait_for(acompletion(**kwargs), timeout=60.0)
                
                self._current_provider = provider_config
                
                if stream:
                    return self._stream_generator(response)
                
                if return_full_object:
                    return response
                else:
                    return response.choices[0].message.content

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"LLM_CALL failed with provider {provider_config.get('model')}: {error_msg}")
                
                fallback_config = self._get_next_fallback()
                if fallback_config:
                    logger.info(f"Attempting fallback to provider: {fallback_config['model']}")
                    provider_config = fallback_config
                else:
                    logger.error(f"All providers exhausted, last error: {error_msg}")
                    err_msg = f"Erreur de communication avec mon cerveau: {error_msg}"
                    return self._error_generator(err_msg) if stream else err_msg

    def get_usage_from_response(self, response) -> dict:
        """Extract token usage from LLM response."""
        if hasattr(response, 'usage') and response.usage:
            return {
                "input_tokens": response.usage.prompt_tokens or 0,
                "output_tokens": response.usage.completion_tokens or 0,
                "total_tokens": response.usage.total_tokens or 0,
            }
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def get_model_provider(self) -> tuple[str, str]:
        """Get provider and model from the model string."""
        model = self.model
        if "/" in model:
            provider, model = model.split("/", 1)
            return provider, model
        return "unknown", model

    async def _error_generator(self, msg: str):
        yield msg

    async def _stream_generator(self, response):
        """Helper to yield content chunks from the stream."""
        async for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content is not None:
                yield delta.content
            elif hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                yield delta.reasoning_content

    async def get_embedding(self, text: str) -> list[float]:
        """
        Generate a vector embedding for the given text using local FastEmbed model.
        Returns a list of floats (dimension 384 for MiniLM).
        """
        if not text: return []
        
        # 1. Check Cache
        if self.cache:
            cached = await self.cache.get(text)
            if cached:
                logger.info(f"Embedding cache hit.")
                return cached

        # 2. Generate Locally
        if self.embedding_model:
            try:
                # FastEmbed returns a generator of vectors (numpy or list)
                embeddings = list(self.embedding_model.embed([text]))
                if embeddings:
                    # Convert numpy array to list if necessary
                    vec = embeddings[0].tolist() if hasattr(embeddings[0], 'tolist') else list(embeddings[0])
                    
                    # 3. Store in Cache
                    if self.cache:
                        await self.cache.set(text, vec)
                    
                    return vec
            except Exception as e:
                logger.error(f"FastEmbed generation failed: {e}")
        
        logger.error("No embedding model available.")
        return []
        