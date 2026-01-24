import os
import logging
from typing import List, Dict, Any, AsyncGenerator, Union, Optional

try:
    import litellm
    from litellm import acompletion, aembedding
    LITELLM_AVAILABLE = True
except ImportError:
    litellm = None
    acompletion = None
    aembedding = None
    LITELLM_AVAILABLE = False
    print("WARNING: litellm library not found. LLM features will be disabled.")

logger = logging.getLogger(__name__)

# Configure litellm to drop unknown params (helps with some providers)
if LITELLM_AVAILABLE:
    litellm.drop_params = True

class LlmClient:
    def __init__(self, cache: Optional[Any] = None):
        self.model = os.getenv("LLM_MODEL", "ollama/mistral")
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.cache = cache
        
        # Ensure provider-specific keys are in environment for LiteLLM
        if os.getenv("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
            logger.info("Gemini API Key detected.")
        if os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
            logger.info(f"OpenRouter API Key detected. Using Model: {self.model}")
        
        if not LITELLM_AVAILABLE:
            logger.warning("LiteLLM is NOT available. AI features will be disabled.")
        else:
            logger.info("LiteLLM initialized successfully.")
        
        logger.info(f"Initializing LlmClient with Model: {self.model}")

    async def get_completion(self, messages: List[Dict[str, str]], stream: bool = False, tools: Optional[List[Dict[str, Any]]] = None, return_full_object: bool = False) -> Union[str, AsyncGenerator[str, None], Any]:
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

            if tools:
                kwargs["tools"] = tools

            response = await acompletion(**kwargs)

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
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    async def get_embedding(self, text: str) -> List[float]:
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
            return None