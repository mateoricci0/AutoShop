"""LLM provider abstraction — all providers implement this interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    cost_usd: float
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...

    @abstractmethod
    def default_model(self) -> str: ...
