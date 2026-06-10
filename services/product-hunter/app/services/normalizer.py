import re
import html
from .scrapers.base import ScrapedProduct
from dataclasses import dataclass


@dataclass
class NormalizedProduct:
    title: str
    source: str
    source_url: str | None
    source_product_id: str | None
    description: str | None
    cost: float | None
    recommended_price: float | None
    estimated_margin: float | None  # percentage
    images: list[dict]
    category: str | None
    tags: list[str]
    raw_data: dict
    engagement_summary: str


def normalize(product: ScrapedProduct) -> NormalizedProduct:
    """Normalize scraped product to standard fields."""
    title = _clean_text(product.title)[:255]
    description = _clean_text(product.description)[:2000] if product.description else None

    # Price estimation
    cost = product.cost
    retail = product.retail_price
    recommended_price = None
    estimated_margin = None

    if cost and cost > 0:
        # Typical dropship markup: 2.5x - 3x
        recommended_price = round(cost * 2.8, 2)
        estimated_margin = round(((recommended_price - cost) / recommended_price) * 100, 1)
    elif retail and retail > 0:
        # If only retail price, estimate cost at 30% of retail
        cost = round(retail * 0.30, 2)
        recommended_price = retail
        estimated_margin = round(((retail - cost) / retail) * 100, 1)

    # Deduplicate images
    seen_urls: set[str] = set()
    clean_images = []
    for img in product.images:
        url = img.get("url", "").strip()
        if url and url not in seen_urls and url.startswith("http"):
            seen_urls.add(url)
            clean_images.append({"url": url, "alt": img.get("alt", title)[:255]})

    # Clean tags
    clean_tags = list(set(
        tag.lower().strip().replace(" ", "-")
        for tag in product.tags
        if tag and len(tag.strip()) > 1
    ))[:20]

    return NormalizedProduct(
        title=title,
        source=product.source,
        source_url=product.source_url,
        source_product_id=product.source_product_id,
        description=description,
        cost=cost,
        recommended_price=recommended_price,
        estimated_margin=estimated_margin,
        images=clean_images[:10],
        category=product.category,
        tags=clean_tags,
        raw_data=product.raw_data,
        engagement_summary=product.to_engagement_summary(),
    )


def _clean_text(text: str | None) -> str:
    if not text:
        return ""
    # Unescape HTML entities
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
