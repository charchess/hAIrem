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

# Configure litellm
if LITELLM_AVAILABLE:
    litellm.drop_params = True
    litellm.success_callback = [] 
    litellm.failure_callback = []

class LlmClient:
    api_key: Any = None
    base_url: Any = None
    embedding_model = None

    def __init__(self, cache: Any | None = None, config_override: dict[str, Any] | None = None):
        config_override = config_override or {}
        self.model = config_override.get("model") or os.getenv("LLM_MODEL", "ollama/mistral")
        
        raw_key = config_override.get("api_key") or os.getenv("LLM_API_KEY")
        self.api_key = str(raw_key) if raw_key else None
        self.base_url = config_override.get("base_url") or os.getenv("LLM_BASE_URL")
        
        self.temperature = config_override.get("temperature")
        self.cache = cache
        
        # Ensure provider-specific keys are in environment for LiteLLM
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            os.environ["OPENROUTER_API_KEY"] = openrouter_key
            logger.info(f"OpenRouter API Key detected. Using Model: {self.model}")
        
        # Initialize Local Embedding Engine
        if FASTEMBED_AVAILABLE:
            try:
                # Default: BAAI/bge-small-en-v1.5 or sentence-transformers/all-MiniLM-L6-v2
                # We use multilingual model for better French support (384 dim)
                self.embedding_model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
                logger.info("FastEmbed initialized with model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 dim)")
            except Exception as e:
                logger.error(f"Failed to initialize FastEmbed: {e}")
        else:
            logger.warning("FastEmbed not available. Embeddings will fail.")
        
        logger.info(f"Initializing LlmClient with Model: {self.model}")

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
        