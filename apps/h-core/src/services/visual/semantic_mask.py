from __future__ import annotations

import base64
import hashlib
import io
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    logger.warning("SemanticMask: Pillow not available — mask generation disabled")

_MASK_CACHE_DIR = os.getenv("MASK_CACHE_DIR", "/tmp/semantic_masks")
os.makedirs(_MASK_CACHE_DIR, exist_ok=True)

SAFE_ZONES: dict[str, list[tuple[float, float, float, float]]] = {
    "Cuisine": [
        (0.0, 0.7, 1.0, 1.0),
        (0.6, 0.3, 1.0, 0.7),
    ],
    "Salon": [
        (0.0, 0.6, 1.0, 1.0),
        (0.1, 0.2, 0.4, 0.6),
    ],
    "Chambre": [
        (0.0, 0.7, 1.0, 1.0),
        (0.3, 0.1, 0.7, 0.5),
    ],
    "Bureau": [
        (0.0, 0.7, 1.0, 1.0),
        (0.0, 0.2, 0.3, 0.7),
    ],
}

EXCLUDED_ZONES: dict[str, list[tuple[float, float, float, float]]] = {
    "Cuisine": [
        (0.2, 0.4, 0.6, 0.7),
    ],
}


def generate_inpainting_mask(
    location: str,
    width: int = 512,
    height: int = 512,
    mode: str = "safe",
) -> str | None:
    if not _PIL_AVAILABLE:
        logger.warning("SemanticMask: Pillow unavailable — returning None")
        return None

    cache_key = hashlib.sha256(f"{location}:{width}:{height}:{mode}".encode()).hexdigest()
    cache_path = os.path.join(_MASK_CACHE_DIR, f"{cache_key}.png")

    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)

    zones = SAFE_ZONES.get(location, []) if mode == "safe" else EXCLUDED_ZONES.get(location, [])

    if not zones:
        zones = [(0.0, 0.5, 1.0, 1.0)]

    for x0, y0, x1, y1 in zones:
        draw.rectangle(
            [int(x0 * width), int(y0 * height), int(x1 * width), int(y1 * height)],
            fill=255,
        )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()

    with open(cache_path, "wb") as f:
        f.write(raw)

    return f"data:image/png;base64,{base64.b64encode(raw).decode()}"


def get_safe_zones(location: str) -> list[tuple[float, float, float, float]]:
    return SAFE_ZONES.get(location, [(0.0, 0.6, 1.0, 1.0)])


def get_excluded_zones(location: str) -> list[tuple[float, float, float, float]]:
    return EXCLUDED_ZONES.get(location, [])
