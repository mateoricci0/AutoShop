"""Stability AI (SDXL) image provider."""
from __future__ import annotations

import time

import httpx
import structlog

from .base import ImageProvider, ImageResult, ImageSize

logger = structlog.get_logger()

_DEFAULT_MODEL = "stable-diffusion-xl-1024-v1-0"
_COST_PER_IMAGE = 0.002  # approx for SDXL 1 step credits

_SIZE_MAP = {
    ImageSize.square:    {"width": 1024, "height": 1024},
    ImageSize.landscape: {"width": 1344, "height": 768},
    ImageSize.portrait:  {"width": 768,  "height": 1344},
}


class StabilityAIProvider(ImageProvider):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url="https://api.stability.ai",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            timeout=120.0,
        )

    def provider_name(self) -> str:
        return "stability"

    def default_model(self) -> str:
        return _DEFAULT_MODEL

    async def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str | None = None,
        size: ImageSize = ImageSize.square,
    ) -> ImageResult:
        dims = _SIZE_MAP[size]
        text_prompts = [{"text": prompt, "weight": 1.0}]
        if negative_prompt:
            text_prompts.append({"text": negative_prompt, "weight": -1.0})

        t0 = time.monotonic()
        resp = await self._client.post(
            f"/v1/generation/{_DEFAULT_MODEL}/text-to-image",
            json={
                "text_prompts": text_prompts,
                "cfg_scale": 7,
                "height": dims["height"],
                "width": dims["width"],
                "samples": 1,
                "steps": 30,
            },
        )
        resp.raise_for_status()
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        import base64
        data = resp.json()
        artifact = data["artifacts"][0]
        image_bytes = base64.b64decode(artifact["base64"])

        return ImageResult(
            image_bytes=image_bytes,
            width=dims["width"],
            height=dims["height"],
            format="png",
            model=_DEFAULT_MODEL,
            provider="stability",
            cost_usd=_COST_PER_IMAGE,
            generation_time_ms=elapsed_ms,
            prompt_used=prompt,
        )

    async def close(self) -> None:
        await self._client.aclose()
