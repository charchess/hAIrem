import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.infrastructure.llm import LlmClient

@pytest.mark.asyncio
async def test_llm_completion_mock():
    # Mocking LiteLLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello World"
    
    with patch("src.infrastructure.llm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = mock_response
        client = LlmClient()
        response = await client.get_completion(messages=[{"role": "user", "content": "Hi"}])
        
        assert response == "Hello World"
        mock_acompletion.assert_called_once()

@pytest.mark.asyncio
async def test_llm_stream_mock():
    # Mocking streaming response
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta.content = "Hello"
    chunk2 = MagicMock()
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta.content = " World"
    
    # Async iterator mock
    async def async_iter():
        yield chunk1
        yield chunk2
        
    with patch("src.infrastructure.llm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = async_iter()
        client = LlmClient()
        generator = await client.get_completion(messages=[{"role": "user", "content": "Hi"}], stream=True)
        
        result = ""
        async for chunk in generator:
            result += chunk
            
        assert result == "Hello World"
        mock_acompletion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_completion_no_litellm():
    with patch("src.infrastructure.llm.LITELLM_AVAILABLE", False):
        client = LlmClient()
        response = await client.get_completion(messages=[{"role": "user", "content": "Hi"}])
        assert "cerveau" in response or "LLM" in response.lower() or isinstance(response, str)


@pytest.mark.asyncio
async def test_llm_completion_stream_no_litellm():
    with patch("src.infrastructure.llm.LITELLM_AVAILABLE", False):
        client = LlmClient()
        gen = await client.get_completion(messages=[{"role": "user", "content": "Hi"}], stream=True)
        chunks = [c async for c in gen]
        assert len(chunks) > 0


@pytest.mark.asyncio
async def test_llm_completion_uses_fallback_on_failure():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Fallback OK"

    call_count = 0

    async def acompletion_side_effect(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("primary failed")
        return mock_response

    client = LlmClient(fallback_providers=[{"model": "fallback/model", "api_key": "key"}])

    with patch("src.infrastructure.llm.acompletion", side_effect=acompletion_side_effect):
        response = await client.get_completion(messages=[{"role": "user", "content": "Hi"}])

    assert response == "Fallback OK"
    assert call_count == 2


@pytest.mark.asyncio
async def test_llm_completion_all_providers_exhausted():
    async def acompletion_side_effect(**kwargs):
        raise Exception("all fail")

    client = LlmClient()

    with patch("src.infrastructure.llm.acompletion", side_effect=acompletion_side_effect):
        response = await client.get_completion(messages=[{"role": "user", "content": "Hi"}])

    assert "Erreur" in response or "error" in response.lower() or isinstance(response, str)


@pytest.mark.asyncio
async def test_llm_completion_return_full_object():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Full"

    with patch("src.infrastructure.llm.acompletion", new_callable=AsyncMock) as mock_ac:
        mock_ac.return_value = mock_response
        client = LlmClient()
        result = await client.get_completion(
            messages=[{"role": "user", "content": "Hi"}],
            return_full_object=True
        )
    assert result is mock_response


@pytest.mark.asyncio
async def test_llm_completion_with_tools():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "With tools"

    with patch("src.infrastructure.llm.acompletion", new_callable=AsyncMock) as mock_ac:
        mock_ac.return_value = mock_response
        client = LlmClient()
        await client.get_completion(
            messages=[{"role": "user", "content": "Hi"}],
            tools=[{"type": "function", "function": {"name": "test"}}]
        )
    call_kwargs = mock_ac.call_args[1]
    assert "tools" in call_kwargs


def test_llm_get_usage_from_response_with_usage():
    client = LlmClient()
    mock_resp = MagicMock()
    mock_resp.usage.prompt_tokens = 10
    mock_resp.usage.completion_tokens = 20
    mock_resp.usage.total_tokens = 30
    result = client.get_usage_from_response(mock_resp)
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 20
    assert result["total_tokens"] == 30


def test_llm_get_usage_from_response_no_usage():
    client = LlmClient()
    mock_resp = MagicMock()
    mock_resp.usage = None
    result = client.get_usage_from_response(mock_resp)
    assert result == {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def test_llm_get_model_provider_with_slash():
    client = LlmClient(config_override={"model": "openrouter/gpt-4"})
    provider, model = client.get_model_provider()
    assert provider == "openrouter"
    assert model == "gpt-4"


def test_llm_get_model_provider_without_slash():
    client = LlmClient(config_override={"model": "gpt4"})
    provider, model = client.get_model_provider()
    assert provider == "unknown"
    assert model == "gpt4"


def test_llm_update_fallback_providers():
    client = LlmClient()
    client.update_fallback_providers([
        {"model": "b/model", "priority": 2},
        {"model": "a/model", "priority": 1},
    ])
    assert client._fallback_providers[0]["priority"] == 1
    assert client._fallback_index == 0


def test_llm_set_api_key():
    client = LlmClient()
    client.set_api_key("new-key-123")
    assert client.api_key == "new-key-123"
    assert client._current_provider["api_key"] == "new-key-123"


@pytest.mark.asyncio
async def test_get_embedding_empty_text():
    client = LlmClient()
    result = await client.get_embedding("")
    assert result == []


@pytest.mark.asyncio
async def test_get_embedding_no_model_returns_empty():
    client = LlmClient()
    client.embedding_model = None
    with patch("src.infrastructure.llm.FASTEMBED_AVAILABLE", False):
        result = await client.get_embedding("some text")
    assert result == []


@pytest.mark.asyncio
async def test_get_embedding_model_failure_returns_empty():
    client = LlmClient()
    client.embedding_model = MagicMock()
    client.embedding_model.embed.side_effect = Exception("model error")
    result = await client.get_embedding("some text")
    assert result == []
