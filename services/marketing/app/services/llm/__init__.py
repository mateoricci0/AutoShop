"""LLM provider factory."""
from __future__ import annotations

from .base import LLMProvider, LLMResponse, Message
from .deepseek import DeepSeekProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider


def get_primary_provider(settings) -> LLMProvider:  # type: ignore[type-arg]
    name = (settings.LLM_PRIMARY or "deepseek").lower()
    return _build(name, settings)


def get_premium_provider(settings) -> LLMProvider:  # type: ignore[type-arg]
    name = (settings.LLM_PREMIUM or "openai").lower()
    return _build(name, settings)


def _build(name: str, settings) -> LLMProvider:  # type: ignore[type-arg]
    if name == "deepseek":
        return DeepSeekProvider(settings.DEEPSEEK_API_KEY)
    if name == "openai":
        return OpenAIProvider(settings.OPENAI_API_KEY)
    if name in ("anthropic", "claude"):
        return AnthropicProvider(settings.ANTHROPIC_API_KEY)
    raise ValueError(f"Unknown LLM provider: {name}")


__all__ = [
    "LLMProvider", "LLMResponse", "Message",
    "DeepSeekProvider", "OpenAIProvider", "AnthropicProvider",
    "get_primary_provider", "get_premium_provider",
]
