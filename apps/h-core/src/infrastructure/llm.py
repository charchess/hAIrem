import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

try:
    import litellm
    from litellm import acompletion, aembedding
    LITELLM_AVAILABLE = True
except ImportError:
    litellm = None  # type: ignore
    acompletion = None
    aembedding = None
    LITELLM_AVAILABLE = False
    print("WARNING: litellm library not found. LLM features will be disabled.")

logger = logging.getLogger(__name__)

# Configure litellm
if LITELLM_AVAILABLE:
    litellm.drop_params = True
    litellm.success_callback = [] # Disable callbacks like cost tracking
    litellm.failure_callback = []

class LlmClient:
    api_key: Any = None
    base_url: Any = None

    def __init__(self, cache: Any | None = None, config_override: dict[str, Any] | None = None):
        config_override = config_override or {}
        self.model = config_override.get("model") or os.getenv("LLM_MODEL", "ollama/mistral")
        
        # DEBUG: Check api_key type
        print(f"DEBUG: api_key type: {type(self.api_key)} value: {self.api_key}")
        
        raw_key = config_override.get("api_key") or os.getenv("LLM_API_KEY")
        self.api_key = str(raw_key) if raw_key else None
        self.base_url = config_override.get("base_url") or os.getenv("LLM_BASE_URL")
        
        self.temperature = config_override.get("temperature")
        self.cache = cache
        
        # Ensure provider-specific keys are in environment for LiteLLM
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
            logger.info("Gemini API Key detected.")
            
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            os.environ["OPENROUTER_API_KEY"] = openrouter_key
            logger.info(f"OpenRouter API Key detected. Using Model: {self.model}")
        
        if not LITELLM_AVAILABLE:
            logger.warning("LiteLLM is NOT available. AI features will be disabled.")
        else:
            logger.info("LiteLLM initialized successfully.")
        
        logger.info(f"Initializing LlmClient with Model: {self.model} (Temp: {self.temperature})")

    async def get_completion(self, messages: list[dict[str, str]], stream: bool = False, tools: list[dict[str, Any]] | None = None, return_full_object: bool = False) -> str | AsyncGenerator[str, None] | Any:
        """
        Get completion from the LLM using litellm.
        """
        if not LITELLM_AVAILABLE:
            err_msg = "Mon cerveau (LLM) n'est pas encore branché."
            return self._error_generator(err_msg) if stream else err_msg

        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "stream": stream
            }
            
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["base_url"] = self.base_url
            if self.temperature is not None:
                kwargs["temperature"] = float(self.temperature)

            if tools:
                kwargs["tools"] = tools

            logger.info(f"LLM_CALL: Model={self.model}, Tools={len(tools) if tools else 0}")
            response = await asyncio.wait_for(acompletion(**kwargs), timeout=60.0)
            logger.info(f"LLM_RESPONSE_RECEIVED: {type(response)}")

            if stream:
                return self._stream_generator(response)
            
            if return_full_object:
                return response
            else:
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Unexpected error during LLM inference: {e}")
            err_msg = f"Erreur de communication avec mon cerveau: {str(e)}"
            return self._error_generator(err_msg) if stream else err_msg

    async def _error_generator(self, msg: str):
        yield msg

    async def _stream_generator(self, response):
        """Helper to yield content chunks from the stream."""
        async for chunk in response:
            delta = chunk.choices[0].delta
            # Capture standard content
            if hasattr(delta, 'content') and delta.content is not None:
                yield delta.content
            # Capture Grok reasoning content if standard content is empty
            elif hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                yield delta.reasoning_content

    async def get_embedding(self, text: str) -> list[float]:
        """
        Generate a vector embedding for the given text.
        """
        if not LITELLM_AVAILABLE or not text: return []
        
        # 1. Check Cache
        if self.cache:
            cached = await self.cache.get(text)
            if cached:
                logger.info(f"Embedding cache hit for: {text[:30]}...")
                return cached

        # 2. Call Provider
        logger.info(f"get_embedding called for text: {text[:50]}...")
        try:
            # FORCE GEMINI EMBEDDING since we have the key
            model = os.getenv("EMBEDDING_MODEL", "gemini/text-embedding-004")
            
            logger.info(f"Generating embedding using model: {model}")
            response = await aembedding(
                model=model,
                input=[text]
            )
            emb = response.data[0]['embedding']
            logger.info(f"Successfully generated embedding of length {len(emb)}")
            
            # 3. Store in Cache
            if self.cache:
                await self.cache.set(text, emb)
                
            return emb
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None  # type: ignore
        