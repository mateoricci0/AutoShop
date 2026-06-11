"""Orchestrates all LLM calls to produce a complete MarketingAsset."""
from __future__ import annotations

import os
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader

from .llm import LLMProvider, Message
from .context_builder import ProductContext
from .output_parsers import parse_json_response, merge_generation_results
from .quality_validator import validate_asset

logger = structlog.get_logger()

_TEMPLATES_DIR = Path(__file__).parent / "prompt_templates"


class MarketingGenerator:
    def __init__(self, provider: LLMProvider, temperature: float = 0.7) -> None:
        self._provider = provider
        self._temperature = temperature
        self._jinja = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=False,
        )

    async def generate(self, ctx: ProductContext) -> dict:
        """Run all 5 generation steps and return merged asset dict + metadata."""
        product_dict = ctx.as_dict()
        total_tokens = 0
        total_cost = 0.0
        model_used = self._provider.default_model()

        # Step 1: branding
        branding = await self._run_template("branding.j2", {"product": product_dict})
        total_tokens += branding["_tokens"]
        total_cost += branding["_cost"]
        model_used = branding["_model"]

        # Step 2: description (needs brand context)
        desc_ctx = {
            "product": product_dict,
            "brand_name": branding.get("brand_name"),
        }
        description = await self._run_template("description.j2", desc_ctx)
        total_tokens += description["_tokens"]
        total_cost += description["_cost"]

        # Step 3: SEO
        seo_ctx = {
            "product": product_dict,
            "brand_name": branding.get("brand_name"),
            "short_description": description.get("short_description"),
        }
        seo = await self._run_template("seo.j2", seo_ctx)
        total_tokens += seo["_tokens"]
        total_cost += seo["_cost"]

        # Step 4: ad copy
        ad_ctx = {
            "product": product_dict,
            "brand_name": branding.get("brand_name"),
            "tagline": branding.get("tagline"),
            "short_description": description.get("short_description"),
            "uvp": branding.get("unique_value_proposition"),
        }
        ad_copy = await self._run_template("ad_copy.j2", ad_ctx)
        total_tokens += ad_copy["_tokens"]
        total_cost += ad_copy["_cost"]

        # Step 5: platform-specific ads
        plat_ctx = {
            "product": product_dict,
            "brand_name": branding.get("brand_name"),
            "short_description": description.get("short_description"),
            "hooks": ad_copy.get("hooks", []),
            "headlines": ad_copy.get("headlines", []),
            "ctas": ad_copy.get("ctas", []),
        }
        platform = await self._run_template("ads_platform.j2", plat_ctx)
        total_tokens += platform["_tokens"]
        total_cost += platform["_cost"]

        merged = merge_generation_results(branding, description, seo, ad_copy, platform)
        validation = validate_asset(merged)

        if not validation.valid:
            logger.warning(
                "asset_validation_failed",
                missing=validation.missing_fields,
                product=ctx.title,
            )

        merged["_tokens_used"] = total_tokens
        merged["_cost_usd"] = total_cost
        merged["_model"] = model_used
        merged["_validation"] = {
            "valid": validation.valid,
            "missing_fields": validation.missing_fields,
            "warnings": validation.warnings,
        }

        return merged

    async def _run_template(self, template_name: str, context: dict) -> dict:
        """Render a Jinja2 template, call the LLM, parse the result."""
        template = self._jinja.get_template(template_name)
        prompt = template.render(**context)

        messages = [Message(role="user", content=prompt)]
        response = await self._provider.complete(
            messages,
            temperature=self._temperature,
            max_tokens=2048,
        )

        result = parse_json_response(response.content)
        result["_tokens"] = response.tokens_used
        result["_cost"] = response.cost_usd
        result["_model"] = response.model
        return result
