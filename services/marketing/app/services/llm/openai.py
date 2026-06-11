"""OpenAI LLM provider."""
from __future__ import annotations

import httpx
import structlog

from .base import LLMProvider, LLMResponse, Message

logger = structlog.get_logger()

_COST_TABLE: dict[str, tuple[float, float]] = {
    "gpt-4o":       (2.50, 10.00),
    "gpt-4o-mini":  (0.15,  0.60),
    "gpt-4-turbo":  (10.00, 30.00),
}
_DEFAULT_MODEL = "gpt-4o-mini"
_BASE_URL = "https://api.openai.com"


class OpenAIProvider(LLMProvider):
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
        in_tok = usage.get("prompt_tokens", 0)
        out_tok = usage.get("completion_tokens", 0)
        in_cost, out_cost = _COST_TABLE.get(resolved_model, (2.50, 10.00))
        cost = (in_tok * in_cost + out_tok * out_cost) / 1_000_000

        return LLMResponse(
            content=content,
            model=resolved_model,
            tokens_used=in_tok + out_tok,
            cost_usd=cost,
            raw=data,
        )

    async def close(self) -> None:
        await self._client.aclose()
