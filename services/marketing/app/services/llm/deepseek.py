"""DeepSeek LLM provider (OpenAI-compatible API)."""
from __future__ import annotations

import httpx
import structlog

from .base import LLMProvider, LLMResponse, Message

logger = structlog.get_logger()

# Approximate cost per 1M tokens (input/output) — update as pricing changes
_COST_PER_1M_INPUT = 0.14   # USD
_COST_PER_1M_OUTPUT = 0.28  # USD

_BASE_URL = "https://api.deepseek.com"
_DEFAULT_MODEL = "deepseek-chat"


class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )

    def default_model(self) -> str:
        return _DEFAULT_MODEL

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        resolved_model = model or _DEFAULT_MODEL
        payload = {
            "model": resolved_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = await self._client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cost = (input_tokens * _COST_PER_1M_INPUT + output_tokens * _COST_PER_1M_OUTPUT) / 1_000_000

        return LLMResponse(
            content=content,
            model=resolved_model,
            tokens_used=input_tokens + output_tokens,
            cost_usd=cost,
            raw=data,
        )

    async def close(self) -> None:
        await self._client.aclose()
