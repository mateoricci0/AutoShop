"""Image provider factory."""
from __future__ import annotations

from .base import ImageProvider, ImageResult, ImageSize
from .openai_dalle import OpenAIDALLEProvider
from .stability_ai import StabilityAIProvider


def get_provider(settings) -> ImageProvider:  # type: ignore[type-arg]
    if settings.STABILITY_API_KEY:
        return StabilityAIProvider(settings.STABILITY_API_KEY)
    return OpenAIDALLEProvider(settings.OPENAI_API_KEY)


__all__ = [
    "ImageProvider", "ImageResult", "ImageSize",
    "OpenAIDALLEProvider", "StabilityAIProvider",
    "get_provider",
]
