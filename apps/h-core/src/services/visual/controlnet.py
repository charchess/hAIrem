from __future__ import annotations

import logging
from typing import Any

from src.services.visual.provider import VisualProvider

logger = logging.getLogger(__name__)

try:
    import httpx as _httpx

    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

_CONTROLNET_MODELS = {
    "depth": "lllyasviel/control_v11f1p_sd15_depth",
    "canny": "lllyasviel/control_v11p_sd15_canny",
    "inpaint": "lllyasviel/control_v11p_sd15_inpaint",
}


class ControlNetProvider(VisualProvider):
    def __init__(
        self,
        base_url: str | None = None,
        controlnet_model: str = "depth",
        api_key: str | None = None,
    ):
        import os

        self.base_url = base_url or os.getenv("CONTROLNET_URL", "http://localhost:7860")
        self.controlnet_model = _CONTROLNET_MODELS.get(controlnet_model, controlnet_model)
        self.api_key = api_key
        self._available: bool | None = None

    async def _check_availability(self) -> bool:
        if not _HTTPX_AVAILABLE:
            return False
        try:
            async with _httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/sdapi/v1/options")
                self._available = resp.status_code == 200
        except Exception:
            self._available = False
        return self._available

    async def generate(
        self,
        prompt: str,
        reference_image: str | None = None,
        control_image: str | None = None,
        mask_image: str | None = None,
        **kwargs: Any,
    ) -> str:
        if not _HTTPX_AVAILABLE:
            logger.warning("ControlNet: httpx unavailable — cannot generate")
            return ""

        if self._available is None:
            await self._check_availability()

        if not self._available:
            logger.warning("ControlNet: endpoint unavailable — skipping generation")
            return ""

        negative_prompt = kwargs.get("negative_prompt", "nsfw, blurry, deformed")
        steps = kwargs.get("steps", 20)
        cfg_scale = kwargs.get("cfg_scale", 7.0)
        width = kwargs.get("width", 512)
        height = kwargs.get("height", 768)

        payload: dict[str, Any] = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height,
            "alwayson_scripts": {},
        }

        if control_image or reference_image:
            control_img = control_image or reference_image
            payload["alwayson_scripts"]["controlnet"] = {
                "args": [
                    {
                        "model": self.controlnet_model,
                        "image": control_img,
                        "weight": kwargs.get("controlnet_weight", 1.0),
                        "guidance_start": kwargs.get("guidance_start", 0.0),
                        "guidance_end": kwargs.get("guidance_end", 1.0),
                        "control_mode": 0,
                    }
                ]
            }

        if mask_image:
            payload["mask"] = mask_image
            payload["inpainting_fill"] = 1
            payload["inpaint_full_res"] = True

        endpoint = "/sdapi/v1/img2img" if (reference_image or mask_image) else "/sdapi/v1/txt2img"

        try:
            async with _httpx.AsyncClient(timeout=120.0) as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                resp = await client.post(f"{self.base_url}{endpoint}", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                images = data.get("images", [])
                if images:
                    return f"data:image/png;base64,{images[0]}"
                logger.error("ControlNet: no images returned")
                return ""
        except Exception as e:
            logger.error(f"ControlNet: generation failed — {e}")
            return ""
