import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.llm import LlmClient

@pytest.mark.asyncio
async def test_llm_completion_mock():
    # Mocking OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello World"
    
    # Mocking the client
    client = LlmClient()
    client.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    response = await client.get_completion(messages=[{"role": "user", "content": "Hi"}])
    
    assert response == "Hello World"
    client.client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_llm_stream_mock():
    # Mocking streaming response
    chunk1 = MagicMock()
    chunk1.choices[0].delta.content = "Hello"
    chunk2 = MagicMock()
    chunk2.choices[0].delta.content = " World"
    
    # Async iterator mock
    async def async_iter():
        yield chunk1
        yield chunk2
        
    client = LlmClient()
    client.client.chat.completions.create = AsyncMock(return_value=async_iter())
    
    generator = await client.get_completion(messages=[{"role": "user", "content": "Hi"}], stream=True)
    
    result = ""
    async for chunk in generator:
        result += chunk
        
    assert result == "Hello World"
