import httpx
import re
from .base import BaseScraper, ScrapedProduct
import structlog

logger = structlog.get_logger()

SEARCH_QUERIES = [
    "viral product 2024", "trending home gadget", "kitchen tool",
    "beauty device", "fitness accessory", "phone holder",
    "led light strip", "portable blender",
]


class AliExpressScraper(BaseScraper):
    name = "aliexpress"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.aliexpress.com/",
        "Accept": "application/json, text/plain, */*",
    }

    async def scrape(self, limit: int = 20) -> list[ScrapedProduct]:
        products = []
        per_query = max(3, limit // len(SEARCH_QUERIES))

        async with httpx.AsyncClient(headers=self.HEADERS, timeout=20.0, follow_redirects=True) as client:
            for query in SEARCH_QUERIES[:5]:
                if len(products) >= limit:
                    break
                try:
                    resp = await client.get(
                        "https://www.aliexpress.com/wholesale",
                        params={
                            "SearchText": query,
                            "sortType": "total_tranpro_desc",
                            "page": 1,
                        },
                    )
                    if resp.status_code != 200:
                        continue

                    # AliExpress returns HTML — parse with BeautifulSoup
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, "lxml")

                    # Find product cards (selector varies — use multiple fallbacks)
                    items = (
                        soup.select("div[class*='product-snippet']")
                        or soup.select("div[class*='item-content']")
                        or soup.select("a[class*='manhattan--container']")
                    )

                    for item in items[:per_query]:
                        try:
                            title_el = item.select_one(
                                "h3[class*='title'], div[class*='title'], span[class*='title']"
                            )
                            if not title_el:
                                continue
                            title = title_el.get_text(strip=True)[:255]

                            price_el = item.select_one("[class*='price']")
                            price_text = price_el.get_text(strip=True) if price_el else ""
                            price_match = re.search(r"[\d.]+", price_text.replace(",", ""))
                            price = float(price_match.group()) if price_match else None

                            orders_el = item.select_one("[class*='sold'], [class*='order']")
                            orders_text = orders_el.get_text(strip=True) if orders_el else ""
                            orders_match = re.search(r"[\d,]+", orders_text)
                            orders = int(orders_match.group().replace(",", "")) if orders_match else None

                            img_el = item.select_one("img")
                            img_url = img_el.get("src") or img_el.get("data-src", "") if img_el else ""

                            link_el = item.select_one("a[href*='aliexpress.com/item']")
                            url = link_el.get("href", "") if link_el else ""
                            prod_id = url.split("/item/")[-1].split(".")[0] if "/item/" in url else ""

                            products.append(ScrapedProduct(
                                title=title,
                                source="aliexpress",
                                source_product_id=prod_id or title[:50],
                                source_url=url or None,
                                retail_price=price,
                                cost=price,
                                images=[{"url": img_url, "alt": title}] if img_url else [],
                                category=query,
                                tags=["aliexpress", "dropship"],
                                sales_count=orders,
                                raw_data={
                                    "price": price,
                                    "orders": orders,
                                    "query": query,
                                },
                            ))
                        except Exception as e:
                            logger.debug("aliexpress_item_error", error=str(e))
                except Exception as e:
                    logger.warning("aliexpress_query_failed", query=query, error=str(e))

        return products
