"""OpenAI DALL-E 3 image provider."""
from __future__ import annotations

import base64
import time

import httpx
import structlog

from .base import ImageProvider, ImageResult, ImageSize

logger = structlog.get_logger()

# DALL-E 3 pricing per image (standard quality)
_COST_TABLE = {
    "1024x1024":  0.040,
    "1792x1024":  0.080,
    "1024x1792":  0.080,
}
_DEFAULT_MODEL = "dall-e-3"


class OpenAIDALLEProvider(ImageProvider):
    def __init__(self, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://api.openai.com",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120.0,
        )

    def provider_name(self) -> str:
        return "openai"

    def default_model(self) -> str:
        return _DEFAULT_MODEL

    async def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str | None = None,
        size: ImageSize = ImageSize.square,
    ) -> ImageResult:
        # DALL-E 3 doesn't support negative prompts natively — append as avoidance instruction
        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt}\n\nAvoid: {negative_prompt}"

        t0 = time.monotonic()
        resp = await self._client.post(
            "/v1/images/generations",
            json={
                "model": _DEFAULT_MODEL,
                "prompt": full_prompt,
                "n": 1,
                "size": size.value,
                "response_format": "b64_json",
                "quality": "standard",
            },
        )
        resp.raise_for_status()
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        data = resp.json()
        b64 = data["data"][0]["b64_json"]
        image_bytes = base64.b64decode(b64)

        w, h = (int(d) for d in size.value.split("x"))
        cost = _COST_TABLE.get(size.value, 0.040)

        return ImageResult(
            image_bytes=image_bytes,
            width=w,
            height=h,
            format="png",
            model=_DEFAULT_MODEL,
            provider="openai",
            cost_usd=cost,
            generation_time_ms=elapsed_ms,
            prompt_used=full_prompt,
        )

    async def close(self) -> None:
        await self._client.aclose()
