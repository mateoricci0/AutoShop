"""Image provider abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class ImageSize(str, Enum):
    square = "1024x1024"
    landscape = "1792x1024"
    portrait = "1024x1792"


@dataclass
class ImageResult:
    image_bytes: bytes
    width: int
    height: int
    format: str   # "png" | "webp" | "jpeg"
    model: str
    provider: str
    cost_usd: float
    generation_time_ms: int
    prompt_used: str


class ImageProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str | None = None,
        size: ImageSize = ImageSize.square,
    ) -> ImageResult: ...

    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def default_model(self) -> str: ...
