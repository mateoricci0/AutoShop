"""Generate optimized image prompts for each of the 7 image types."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


IMAGE_TYPES = ["hero", "lifestyle", "infographic", "before_after", "banner", "ad_square", "ad_story"]


@dataclass
class ImagePromptSpec:
    image_type: str
    prompt: str
    negative_prompt: str
    size: str  # "square" | "landscape" | "portrait"


_NEGATIVE_BASE = (
    "blurry, low quality, distorted, watermark, text overlay, logo, bad anatomy, "
    "poorly drawn, extra limbs, deformed, ugly, duplicate, out of frame"
)


def generate_prompts(
    product_title: str,
    category: str | None,
    description: str | None,
    brand_name: str | None = None,
    tagline: str | None = None,
) -> list[ImagePromptSpec]:
    """Return one ImagePromptSpec for each of the 7 image types."""
    cat = category or "product"
    desc = description or ""
    brand = brand_name or ""
    short_desc = desc[:120] if desc else ""

    return [
        ImagePromptSpec(
            image_type="hero",
            prompt=(
                f"Professional product photography of {product_title}, {cat}. "
                f"Studio lighting, clean white background, ultra-sharp focus, "
                f"commercial product shot, 8K resolution, photorealistic"
            ),
            negative_prompt=_NEGATIVE_BASE + ", cluttered background, shadows",
            size="square",
        ),
        ImagePromptSpec(
            image_type="lifestyle",
            prompt=(
                f"Lifestyle photography featuring {product_title} in natural use. "
                f"Happy person using the product in a modern, aspirational setting. "
                f"Natural light, warm tones, authentic feel, editorial style, cinematic"
            ),
            negative_prompt=_NEGATIVE_BASE + ", studio backdrop, artificial look",
            size="landscape",
        ),
        ImagePromptSpec(
            image_type="infographic",
            prompt=(
                f"Clean product infographic for {product_title}. "
                f"Minimal flat design, feature icons with labels, bold typography, "
                f"white background, professional product marketing layout"
            ),
            negative_prompt=_NEGATIVE_BASE + ", photorealistic, 3D render",
            size="square",
        ),
        ImagePromptSpec(
            image_type="before_after",
            prompt=(
                f"Before and after comparison image for {product_title}. "
                f"Split screen layout, left side shows the problem, right side shows "
                f"the improved result using the product. Clean, professional design"
            ),
            negative_prompt=_NEGATIVE_BASE,
            size="landscape",
        ),
        ImagePromptSpec(
            image_type="banner",
            prompt=(
                f"Wide promotional banner for {product_title}. "
                f"{'Brand: ' + brand + '.' if brand else ''} "
                f"Bold colors, modern design, product featured prominently, "
                f"e-commerce marketing banner style"
            ),
            negative_prompt=_NEGATIVE_BASE + ", portrait orientation",
            size="landscape",
        ),
        ImagePromptSpec(
            image_type="ad_square",
            prompt=(
                f"Square social media ad image for {product_title}. "
                f"Eye-catching design, product as hero, minimal text space, "
                f"vibrant colors, Instagram/Facebook ad style, professional"
            ),
            negative_prompt=_NEGATIVE_BASE,
            size="square",
        ),
        ImagePromptSpec(
            image_type="ad_story",
            prompt=(
                f"Vertical social media story ad for {product_title}. "
                f"Mobile-first vertical format, full bleed product imagery, "
                f"TikTok/Instagram Stories style, engaging, dynamic composition"
            ),
            negative_prompt=_NEGATIVE_BASE + ", landscape orientation",
            size="portrait",
        ),
    ]
