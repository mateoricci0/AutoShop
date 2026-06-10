import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, ScrapedProduct
import structlog
import re

logger = structlog.get_logger()


class TemuScraper(BaseScraper):
    name = "temu"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/html",
    }

    SEARCH_QUERIES = ["trending", "bestseller", "new arrivals"]

    async def scrape(self, limit: int = 20) -> list[ScrapedProduct]:
        products = []
        async with httpx.AsyncClient(headers=self.HEADERS, timeout=20.0, follow_redirects=True) as client:
            for query in self.SEARCH_QUERIES:
                if len(products) >= limit:
                    break
                try:
                    resp = await client.get(
                        "https://www.temu.com/search_result.html",
                        params={"search_key": query, "search_type": "goods"},
                    )
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "lxml")
                    items = soup.select("[class*='product-item'], [class*='goods-item']")[:10]

                    for item in items:
                        try:
                            title_el = item.select_one("[class*='title'], [class*='name']")
                            if not title_el:
                                continue
                            title = title_el.get_text(strip=True)[:255]

                            price_el = item.select_one("[class*='price']")
                            price_text = price_el.get_text(strip=True) if price_el else ""
                            price_match = re.search(r"[\d.]+", price_text.replace(",", ""))
                            price = float(price_match.group()) if price_match else None

                            img_el = item.select_one("img")
                            img_url = img_el.get("src") or img_el.get("data-src", "") if img_el else ""

                            products.append(ScrapedProduct(
                                title=title,
                                source="temu",
                                source_product_id=title[:50],
                                retail_price=price,
                                cost=price,
                                images=[{"url": img_url, "alt": title}] if img_url else [],
                                category=query,
                                tags=["temu", "trending"],
                                raw_data={"price": price, "query": query},
                            ))
                        except Exception as e:
                            logger.debug("temu_item_error", error=str(e))
                except Exception as e:
                    logger.warning("temu_query_failed", query=query, error=str(e))
        return products
