import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, ScrapedProduct
import structlog
import re

logger = structlog.get_logger()

CATEGORIES = {
    "home-kitchen": "Home & Kitchen",
    "health-personal-care": "Health & Personal Care",
    "beauty": "Beauty",
    "sports-outdoors": "Sports & Outdoors",
    "tools-home-improvement": "Tools & Home Improvement",
    "pet-supplies": "Pet Supplies",
    "baby-products": "Baby Products",
    "electronics": "Electronics",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}


class AmazonScraper(BaseScraper):
    name = "amazon"

    async def scrape(self, limit: int = 20) -> list[ScrapedProduct]:
        products = []
        per_cat = max(3, limit // len(CATEGORIES))

        async with httpx.AsyncClient(headers=HEADERS, timeout=20.0, follow_redirects=True) as client:
            for slug, cat_name in list(CATEGORIES.items())[:5]:
                if len(products) >= limit:
                    break
                try:
                    resp = await client.get(
                        f"https://www.amazon.com/gp/movers-and-shakers/{slug}",
                    )
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "lxml")
                    items = soup.select("div.zg-item-immersion")[:per_cat]

                    for item in items:
                        try:
                            title_el = item.select_one("div.p13n-sc-truncate, a.a-link-normal span")
                            if not title_el:
                                continue
                            title = title_el.get_text(strip=True)

                            rank_el = item.select_one("span.zg-bdg-text")
                            rank = int(rank_el.get_text(strip=True).replace("#", "")) if rank_el else 999

                            price_el = item.select_one("span.p13n-sc-price, span._cDEzb_p13n-sc-price_3mJ9Z")
                            price_text = price_el.get_text(strip=True) if price_el else ""
                            price = float(re.sub(r"[^\d.]", "", price_text)) if price_text else None

                            img_el = item.select_one("img.s-image, img.a-dynamic-image")
                            img_url = img_el.get("src", "") if img_el else ""

                            asin_el = item.select_one("a.a-link-normal[href*='/dp/']")
                            asin = ""
                            if asin_el:
                                m = re.search(r"/dp/([A-Z0-9]{10})", asin_el.get("href", ""))
                                asin = m.group(1) if m else ""

                            products.append(ScrapedProduct(
                                title=title[:255],
                                source="amazon",
                                source_product_id=asin or title[:50],
                                source_url=f"https://amazon.com/dp/{asin}" if asin else None,
                                retail_price=price,
                                cost=round(price * 0.25, 2) if price else None,
                                category=cat_name,
                                tags=["amazon", "movers-shakers", cat_name.lower().replace(" ", "-")],
                                images=[{"url": img_url, "alt": title}] if img_url else [],
                                # Rank → approximate popularity score
                                views=(100 - min(rank, 99)) * 1000,
                                raw_data={
                                    "rank": rank,
                                    "category": cat_name,
                                    "asin": asin,
                                    "price": price,
                                },
                            ))
                        except Exception as e:
                            logger.debug("amazon_item_parse_error", error=str(e))
                except Exception as e:
                    logger.warning("amazon_category_failed", category=slug, error=str(e))

        return products
