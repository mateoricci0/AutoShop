from openai import AsyncOpenAI
from dataclasses import dataclass
import json
import re
import structlog
from .normalizer import NormalizedProduct
from ..config import settings

logger = structlog.get_logger()

SCORE_WEIGHTS = {
    "demand_score":      0.25,
    "trend_score":       0.20,
    "margin_score":      0.20,
    "engagement_score":  0.15,
    "competition_score": 0.10,
    "saturation_score":  0.05,
    "branding_score":    0.05,
}

SCORING_PROMPT = """\
You are an expert e-commerce product analyst specializing in dropshipping.

Analyze this product for dropshipping potential and return ONLY valid JSON.

PRODUCT DATA:
- Title: {title}
- Description: {description}
- Category: {category}
- Source: {source}
- Cost/Price: {price_info}
- Engagement signals: {engagement}
- Additional data: {raw_data_summary}

Return ONLY this JSON object (no markdown, no explanation):
{{
  "demand_score": <integer 0-100, based on market demand evidence>,
  "competition_score": <integer 0-100, 100=no competition, 0=very saturated>,
  "trend_score": <integer 0-100, based on trend direction>,
  "engagement_score": <integer 0-100, based on social engagement signals>,
  "saturation_score": <integer 0-100, 100=not saturated market>,
  "branding_score": <integer 0-100, branding/differentiation potential>,
  "margin_score": <integer 0-100, profit margin potential>,
  "analysis": "<2-3 sentence honest product assessment>",
  "recommended_price": <number in USD or null if unknown>,
  "estimated_margin": <percentage 0-100 or null>
}}

Be realistic and critical. Most products should score 40-70. Only exceptional products score above 80.\
"""


@dataclass
class ScoringResult:
    demand_score: float
    competition_score: float
    trend_score: float
    engagement_score: float
    saturation_score: float
    branding_score: float
    margin_score: float
    success_score: float
    analysis: str
    recommended_price: float | None
    estimated_margin: float | None
    model: str
    tokens_used: int
    cost_usd: float


def _compute_success_score(scores: dict) -> float:
    total = sum(scores[k] * w for k, w in SCORE_WEIGHTS.items() if k in scores)
    return round(min(100.0, max(0.0, total)), 2)


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    # DeepSeek-chat pricing (as of 2024)
    if "deepseek" in model.lower():
        return (input_tokens * 0.14 + output_tokens * 0.28) / 1_000_000
    # GPT-4o-mini fallback
    return (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000


class ProductScorer:
    def __init__(self):
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            if settings.LLM_PRIMARY == "deepseek" and settings.DEEPSEEK_API_KEY:
                self._client = AsyncOpenAI(
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url=settings.DEEPSEEK_BASE_URL,
                )
            elif settings.OPENAI_API_KEY:
                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            else:
                raise RuntimeError("No AI API key configured. Set DEEPSEEK_API_KEY or OPENAI_API_KEY.")
        return self._client

    def _get_model(self) -> str:
        if settings.LLM_PRIMARY == "deepseek" and settings.DEEPSEEK_API_KEY:
            return settings.DEEPSEEK_MODEL
        return "gpt-4o-mini"

    async def score(self, product: NormalizedProduct) -> ScoringResult:
        client = self._get_client()
        model = self._get_model()

        price_info = "unknown"
        if product.cost:
            price_info = f"cost ${product.cost:.2f}"
            if product.recommended_price:
                price_info += f", selling price ${product.recommended_price:.2f}"

        raw_summary = json.dumps({
            k: v for k, v in list(product.raw_data.items())[:8]
            if not isinstance(v, (bytes, bytearray))
        }, default=str)[:500]

        prompt = SCORING_PROMPT.format(
            title=product.title,
            description=(product.description or "N/A")[:300],
            category=product.category or "unknown",
            source=product.source,
            price_info=price_info,
            engagement=product.engagement_summary,
            raw_data_summary=raw_summary,
        )

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=600,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        usage = response.usage
        tokens_used = usage.total_tokens if usage else 0
        cost = _estimate_cost(
            model,
            usage.prompt_tokens if usage else 0,
            usage.completion_tokens if usage else 0,
        )

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try extracting JSON from response
            match = re.search(r"\{.*\}", content, re.DOTALL)
            data = json.loads(match.group()) if match else {}

        scores = {
            "demand_score":      float(data.get("demand_score", 50)),
            "competition_score": float(data.get("competition_score", 50)),
            "trend_score":       float(data.get("trend_score", 50)),
            "engagement_score":  float(data.get("engagement_score", 50)),
            "saturation_score":  float(data.get("saturation_score", 50)),
            "branding_score":    float(data.get("branding_score", 50)),
            "margin_score":      float(data.get("margin_score", 50)),
        }
        # Clamp all scores to 0-100
        scores = {k: min(100.0, max(0.0, v)) for k, v in scores.items()}

        return ScoringResult(
            **scores,
            success_score=_compute_success_score(scores),
            analysis=str(data.get("analysis", ""))[:500],
            recommended_price=float(data["recommended_price"]) if data.get("recommended_price") else product.recommended_price,
            estimated_margin=float(data["estimated_margin"]) if data.get("estimated_margin") else product.estimated_margin,
            model=model,
            tokens_used=tokens_used,
            cost_usd=cost,
        )


# Module-level singleton
_scorer: ProductScorer | None = None


def get_scorer() -> ProductScorer:
    global _scorer
    if _scorer is None:
        _scorer = ProductScorer()
    return _scorer
