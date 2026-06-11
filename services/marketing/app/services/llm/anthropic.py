"""Anthropic LLM provider (Claude)."""
from __future__ import annotations

import httpx
import structlog

from .base import LLMProvider, LLMResponse, Message

logger = structlog.get_logger()

_COST_TABLE: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (0.80,  4.00),
    "claude-sonnet-4-6":         (3.00, 15.00),
    "claude-opus-4-8":           (15.00, 75.00),
}
_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_BASE_URL = "https://api.anthropic.com"
_API_VERSION = "2023-06-01"


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": _API_VERSION,
                "content-type": "application/json",
            },
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

        # Anthropic separates system from conversation messages
        system_parts = [m.content for m in messages if m.role == "system"]
        conv = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]

        payload: dict = {
            "model": resolved_model,
            "messages": conv,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)

        resp = await self._client.post("/v1/messages", json=payload)
        resp.raise_for_status()
        data = resp.json()

        content = data["content"][0]["text"]
        usage = data.get("usage", {})
        in_tok = usage.get("input_tokens", 0)
        out_tok = usage.get("output_tokens", 0)
        in_cost, out_cost = _COST_TABLE.get(resolved_model, (3.00, 15.00))
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
