import os
import logging
from typing import List, Dict, Any, AsyncGenerator, Union, Optional
from openai import AsyncOpenAI, APIError, APITimeoutError

logger = logging.getLogger(__name__)

class LlmClient:
    def __init__(self):
        self.base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
        self.api_key = os.getenv("LLM_API_KEY", "ollama") # Ollama doesn't need a real key
        self.model = os.getenv("LLM_MODEL", "mistral")
        
        logger.info(f"Initializing LlmClient with URL: {self.base_url}, Model: {self.model}")
        
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=30.0 # Default timeout
        )

    async def get_completion(self, messages: List[Dict[str, str]], stream: bool = False, tools: Optional[List[Dict[str, Any]]] = None, return_full_object: bool = False) -> Union[str, AsyncGenerator[str, None], Any]:
        """
        Get completion from the LLM.
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "stream": stream
            }
            if tools:
                kwargs["tools"] = tools

            response = await self.client.chat.completions.create(**kwargs)

            if stream:
                return self._stream_generator(response)
            
            if return_full_object:
                return response
            else:
                return response.choices[0].message.content

        except APITimeoutError:
            logger.error("LLM request timed out.")
            err_msg = "Désolé, je mets trop de temps à réfléchir."
            return self._error_generator(err_msg) if stream else err_msg
        except APIError as e:
            logger.error(f"LLM API Error: {e}")
            err_msg = f"Erreur de communication avec mon cerveau: {str(e)}"
            return self._error_generator(err_msg) if stream else err_msg
        except Exception as e:
            logger.error(f"Unexpected error during LLM inference: {e}")
            err_msg = "Une erreur inattendue est survenue."
            return self._error_generator(err_msg) if stream else err_msg

    async def _error_generator(self, msg: str):
        yield msg

    async def _stream_generator(self, response):
        """Helper to yield content chunks from the stream."""
        async for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
