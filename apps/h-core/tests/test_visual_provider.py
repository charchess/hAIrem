import pytest
import httpx
import os
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.visual.provider import NanoBananaProvider, VisualProvider, ImagenV2Provider

@pytest.mark.asyncio
async def test_nanobanana_inheritance():
    """Verify NanoBananaProvider inherits from VisualProvider."""
    provider = NanoBananaProvider(api_key="test")
    assert isinstance(provider, VisualProvider)

@pytest.mark.asyncio
async def test_nanobanana_generate_success():
    """Test successful image generation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"url": "http://example.com/image.png"}
    mock_response.raise_for_status = MagicMock()

    # We patch httpx.AsyncClient.post directly
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        provider = NanoBananaProvider(api_key="test_key", base_url="http://test_api")
        url = await provider.generate(prompt="a blue cat", style_preset="pixel-art")
        
        assert url == "http://example.com/image.png"
        
        # Verify the call parameters
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["prompt"] == "a blue cat"
        assert kwargs["json"]["style_preset"] == "pixel-art"
        assert kwargs["headers"]["Authorization"] == "Bearer test_key"
        assert "http://test_api/generate" in args[0]

@pytest.mark.asyncio
async def test_nanobanana_generate_with_reference():
    """Test generation with a reference image."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"url": "http://example.com/ref_image.png"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        provider = NanoBananaProvider()
        url = await provider.generate(
            prompt="same cat", 
            reference_image="http://example.com/base.png"
        )
        
        assert url == "http://example.com/ref_image.png"
        kwargs = mock_post.call_args[1]
        assert kwargs["json"]["reference_image"] == "http://example.com/base.png"

@pytest.mark.asyncio
async def test_nanobanana_generate_http_error():
    """Test handling of HTTP errors."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    
    # Mocking raise_for_status to actually raise
    def raise_error():
        raise httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)
    
    mock_response.raise_for_status.side_effect = raise_error

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        provider = NanoBananaProvider(api_key="wrong_key")
        with pytest.raises(httpx.HTTPStatusError):
            await provider.generate(prompt="test")

@pytest.mark.asyncio
async def test_nanobanana_invalid_response():
    """Test handling of responses missing the expected 'url' field."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"not_a_url": "something"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        provider = NanoBananaProvider()
        with pytest.raises(ValueError, match="missing 'url'"):
            await provider.generate(prompt="test")

@pytest.mark.asyncio
async def test_imagen_v2_generate_success():
    """Test successful image generation with ImagenV2Provider (async polling)."""
    # 1. Mock the /generate response
    mock_gen_response = MagicMock()
    mock_gen_response.status_code = 201
    mock_gen_response.json.return_value = {"job_id": "test-uuid-v4"}
    mock_gen_response.raise_for_status = MagicMock()

    # 2. Mock the /image/{id} polling responses
    # First call: 202 Accepted
    mock_poll_202 = MagicMock()
    mock_poll_202.status_code = 202
    mock_poll_202.json.return_value = {"state": "PROGRESS", "meta": {"progress": 50}}
    
    # Second call: 200 OK
    mock_poll_200 = MagicMock()
    mock_poll_200.status_code = 200
    mock_poll_200.content = b"fake-png-binary-data"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_gen_response
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [mock_poll_202, mock_poll_200]
            
            # Shorten sleep for tests
            with patch("asyncio.sleep", new_callable=AsyncMock):
                provider = ImagenV2Provider(base_url="http://imagen-v2")
                result_url = await provider.generate(prompt="a futuristic city")
                
                assert result_url.startswith("file://")
                local_path = result_url.replace("file://", "")
                assert os.path.exists(local_path)
                
                # Cleanup
                os.remove(local_path)

@pytest.mark.asyncio
async def test_imagen_v2_generate_failure():
    """Test handling of generation failure in ImagenV2Provider."""
    mock_gen_response = MagicMock()
    mock_gen_response.status_code = 201
    mock_gen_response.json.return_value = {"job_id": "fail-uuid"}
    mock_gen_response.raise_for_status = MagicMock()
    
    mock_poll_500 = MagicMock()
    mock_poll_500.status_code = 500
    mock_poll_500.json.return_value = {"detail": {"error": "CUDA out of memory"}}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_gen_response
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_poll_500
            
            provider = ImagenV2Provider()
            with pytest.raises(ValueError, match="CUDA out of memory"):
                await provider.generate(prompt="too complex")

@pytest.mark.asyncio
async def test_imagen_v2_timeout():
    """Test timeout handling when polling takes too long."""
    mock_gen_response = MagicMock()
    mock_gen_response.status_code = 201
    mock_gen_response.json.return_value = {"job_id": "timeout-uuid"}
    mock_gen_response.raise_for_status = MagicMock()
    
    # Always return 202
    mock_poll_202 = MagicMock()
    mock_poll_202.status_code = 202
    mock_poll_202.json.return_value = {"state": "PROGRESS", "meta": {"progress": 10}}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_gen_response
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_poll_202
            
            # Mock sleep to run instantly
            with patch("asyncio.sleep", new_callable=AsyncMock):
                # Reduce max_retries locally for test speed if possible, 
                # or just rely on the fact that we can't easily change the hardcoded 120 loop 
                # without dependency injection. 
                # To avoid running 120 iterations, we can raise an exception from side_effect after N calls
                # OR we accept we need to mock the loop behavior or the class constant if it existed.
                # Since it's hardcoded 120, we'll patch the provider's logic or just mock side_effect to raise TimeoutError
                # But testing the *actual* timeout logic requires iterating 120 times which is slow.
                # BETTER APPROACH: Patch the range or break early.
                
                # Let's trust the logic but maybe test that it raises TimeoutError if loop finishes.
                # To make it fast, we can mock the loop range in the source code or 
                # assume the user wants us to test the *handling* of the loop exit.
                
                # For this test, let's just assert the timeout logic works by mocking the 'range' 
                # but 'range' is a built-in.
                # Instead, let's inject a lower max_retries via a monkeypatch or just run a few loops 
                # and verify it calls sleep?
                # Actually, 120 iterations with mocked sleep is very fast.
                
                provider = ImagenV2Provider()
                
                # We need to ensure it eventually raises TimeoutError. 
                # mocking get 120 times:
                mock_get.return_value = mock_poll_202
                
                with pytest.raises(TimeoutError):
                    await provider.generate(prompt="slow")
                
                # Verify we polled multiple times
                assert mock_get.call_count > 1

@pytest.mark.asyncio
async def test_imagen_v2_not_found():
    """Test handling of 404 during polling (Job ID lost)."""
    mock_gen_response = MagicMock()
    mock_gen_response.status_code = 201
    mock_gen_response.json.return_value = {"job_id": "lost-uuid"}
    
    mock_poll_404 = MagicMock()
    mock_poll_404.status_code = 404
    
    # We need to mock raise_for_status to raise
    def raise_404():
        raise httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_poll_404)
    mock_poll_404.raise_for_status.side_effect = raise_404

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_gen_response
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_poll_404
            
            provider = ImagenV2Provider()
            with pytest.raises(httpx.HTTPStatusError):
                await provider.generate(prompt="lost")

@pytest.mark.asyncio
async def test_imagen_v2_parameter_mapping():
    """Verify all kwargs are correctly mapped to the API payload."""
    mock_gen_response = MagicMock()
    mock_gen_response.status_code = 201
    mock_gen_response.json.return_value = {"job_id": "params-uuid"}
    
    mock_poll_200 = MagicMock()
    mock_poll_200.status_code = 200
    mock_poll_200.content = b"img"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_gen_response
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_poll_200
            
            provider = ImagenV2Provider()
            await provider.generate(
                prompt="detailed view",
                negative_prompt="blur",
                model="pony-xl-v6",
                loras=[{"name": "style", "weight": 1.0}],
                steps=50,
                guidance_scale=8.0,
                seed=12345,
                ip_strength=0.5
            )
            
            args, kwargs = mock_post.call_args
            payload = kwargs["json"]
            
            assert payload["prompt"] == "detailed view"
            assert payload["negative_prompt"] == "blur"
            assert payload["model"] == "pony-xl-v6"
            assert payload["loras"] == [{"name": "style", "weight": 1.0}]
            assert payload["steps"] == 50
            assert payload["guidance_scale"] == 8.0
            assert payload["seed"] == 12345
            assert payload["ip_strength"] == 0.5

@pytest.mark.asyncio
async def test_imagen_v2_env_defaults():
    """Verify that environment variables control default parameters."""
    mock_gen_response = MagicMock()
    mock_gen_response.status_code = 201
    mock_gen_response.json.return_value = {"job_id": "env-defaults-uuid"}
    
    mock_poll_200 = MagicMock()
    mock_poll_200.status_code = 200
    mock_poll_200.content = b"img"

    # Set up environment variables
    env_vars = {
        "IMAGENV2_MODEL": "pony-xl-v6",
        "IMAGENV2_GUIDANCE_SCALE": "5.5",
        "IMAGENV2_LORAS": '[{"name": "env-lora", "weight": 0.5}]',
        "IMAGENV2_IP_STRENGTH": "0.8"
    }

    with patch.dict(os.environ, env_vars):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_gen_response
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_poll_200
                
                provider = ImagenV2Provider()
                
                # Case 1: Standard generation (no reference)
                await provider.generate(prompt="test env")
                args, kwargs = mock_post.call_args
                payload = kwargs["json"]
                
                assert payload["model"] == "pony-xl-v6"
                assert payload["guidance_scale"] == 5.5
                assert payload["loras"] == [{"name": "env-lora", "weight": 0.5}]
                assert payload["ip_strength"] == 0.0 # Should be 0 without reference
                
                # Case 2: With reference image
                await provider.generate(prompt="test ref", reference_image="ref_data")
                args, kwargs = mock_post.call_args
                payload = kwargs["json"]
                
                assert payload["ip_strength"] == 0.8 # Should pick up env default

@pytest.mark.asyncio
async def test_imagen_v2_default_model():
    """Verify the default model is 'sdxl'."""
    mock_gen_response = MagicMock()
    mock_gen_response.status_code = 201
    mock_gen_response.json.return_value = {"job_id": "default-uuid"}
    
    mock_poll_200 = MagicMock()
    mock_poll_200.status_code = 200
    mock_poll_200.content = b"img"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_gen_response
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_poll_200
            
            provider = ImagenV2Provider()
            await provider.generate(prompt="default test")
            
            args, kwargs = mock_post.call_args
            assert kwargs["json"]["model"] == "sdxl"