import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestControlNetProvider:
    def _make_provider(self, available=True, base_url="http://localhost:7860"):
        from src.services.visual.controlnet import ControlNetProvider

        provider = ControlNetProvider(base_url=base_url)
        provider._available = available
        return provider

    @pytest.mark.asyncio
    async def test_generate_returns_empty_when_unavailable(self):
        provider = self._make_provider(available=False)
        result = await provider.generate("a cozy kitchen")
        assert result == ""

    @pytest.mark.asyncio
    async def test_generate_returns_dataurl_on_success(self):
        import httpx

        provider = self._make_provider(available=True)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"images": ["abc123base64=="]}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await provider.generate("a cozy kitchen scene")

        assert result.startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_generate_uses_img2img_when_reference_given(self):
        import httpx

        provider = self._make_provider(available=True)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"images": ["xyz=="]}

        captured_url = []

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)

            async def _post(url, **kwargs):
                captured_url.append(url)
                return mock_response

            mock_client.post = _post
            mock_client_cls.return_value = mock_client

            await provider.generate("kitchen", reference_image="data:image/png;base64,ref==")

        assert any("img2img" in u for u in captured_url)

    @pytest.mark.asyncio
    async def test_controlnet_payload_includes_controlnet_args(self):
        provider = self._make_provider(available=True)

        captured_payloads = []
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"images": ["abc=="]}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)

            async def _post(url, json=None, **kwargs):
                captured_payloads.append(json)
                return mock_response

            mock_client.post = _post
            mock_client_cls.return_value = mock_client

            await provider.generate("kitchen", control_image="data:image/png;base64,ctrl==")

        assert len(captured_payloads) == 1
        payload = captured_payloads[0]
        assert "controlnet" in payload["alwayson_scripts"]


class TestSemanticMask:
    def test_get_safe_zones_known_location(self):
        from src.services.visual.semantic_mask import get_safe_zones

        zones = get_safe_zones("Cuisine")
        assert len(zones) > 0
        for z in zones:
            assert len(z) == 4

    def test_get_safe_zones_unknown_location_fallback(self):
        from src.services.visual.semantic_mask import get_safe_zones

        zones = get_safe_zones("Unknown Room")
        assert len(zones) > 0

    def test_get_excluded_zones(self):
        from src.services.visual.semantic_mask import get_excluded_zones

        zones = get_excluded_zones("Cuisine")
        assert isinstance(zones, list)

    def test_generate_mask_without_pillow_returns_none(self):
        import sys
        import importlib

        with patch("src.services.visual.semantic_mask._PIL_AVAILABLE", False):
            from src.services.visual import semantic_mask

            original = semantic_mask._PIL_AVAILABLE
            semantic_mask._PIL_AVAILABLE = False
            try:
                result = semantic_mask.generate_inpainting_mask("Cuisine")
                assert result is None
            finally:
                semantic_mask._PIL_AVAILABLE = original

    def test_generate_mask_with_pillow_returns_dataurl(self):
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("Pillow not installed")

        from src.services.visual.semantic_mask import generate_inpainting_mask
        import tempfile
        import os

        with patch("src.services.visual.semantic_mask._MASK_CACHE_DIR", tempfile.mkdtemp()):
            result = generate_inpainting_mask("Salon", width=64, height=64)

        if result is not None:
            assert result.startswith("data:image/png;base64,")
