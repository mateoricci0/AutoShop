"""Parse structured JSON from LLM responses, with fallback extraction."""
from __future__ import annotations

import json
import re
import structlog

logger = structlog.get_logger()


def parse_json_response(content: str) -> dict:
    """Extract and parse JSON from LLM response text.

    Handles: raw JSON, ```json ... ``` fences, JSON embedded in text.
    """
    content = content.strip()

    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Extract from fenced code block
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Find first { ... } block in the content
    brace_match = re.search(r"(\{.*\})", content, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(1))
        except json.JSONDecodeError:
            pass

    logger.warning("json_parse_failed", content_preview=content[:200])
    return {}


def merge_generation_results(
    branding: dict,
    description: dict,
    seo: dict,
    ad_copy: dict,
    ads_platform: dict,
) -> dict:
    """Flatten all generation outputs into a single marketing asset dict."""
    return {
        # Branding
        "brand_name": branding.get("brand_name"),
        "tagline": branding.get("tagline"),
        # Description
        "short_description": description.get("short_description"),
        "long_description": description.get("long_description"),
        "bullet_points": description.get("bullet_points", []),
        "faqs": description.get("faqs", []),
        # SEO
        "meta_title": seo.get("meta_title"),
        "meta_description": seo.get("meta_description"),
        "keywords": seo.get("keywords", []),
        "_seo_h1": seo.get("h1_title"),
        "_seo_tags": seo.get("shopify_tags", []),
        "_seo_handle": seo.get("url_handle"),
        "_product_type": seo.get("product_type"),
        # Ad copy
        "hooks": ad_copy.get("hooks", []),
        "headlines": ad_copy.get("headlines", []),
        "ctas": ad_copy.get("ctas", []),
        "ad_copies": ad_copy.get("ad_copies", []),
        # Platform ads
        "facebook_ads": ads_platform.get("facebook_ads", {}),
        "instagram_ads": ads_platform.get("instagram_ads", {}),
        "tiktok_ads": ads_platform.get("tiktok_ads", {}),
        "google_ads": ads_platform.get("google_ads", {}),
        "email_campaigns": ads_platform.get("email_campaigns", {}),
    }
