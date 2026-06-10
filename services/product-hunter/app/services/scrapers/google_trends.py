from pytrends.request import TrendReq
from .base import BaseScraper, ScrapedProduct
import asyncio
import structlog

logger = structlog.get_logger()


class GoogleTrendsScraper(BaseScraper):
    name = "google_trends"

    CATEGORIES = [
        "home improvement", "kitchen gadgets", "beauty products",
        "fitness equipment", "baby products", "pet supplies",
        "phone accessories", "outdoor gear",
    ]

    async def scrape(self, limit: int = 20) -> list[ScrapedProduct]:
        # pytrends is synchronous — run in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._scrape_sync, limit)

    def _scrape_sync(self, limit: int) -> list[ScrapedProduct]:
        products = []
        try:
            pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))

            for category in self.CATEGORIES[:max(3, limit // 5)]:
                try:
                    pytrends.build_payload(
                        [category],
                        cat=0,
                        timeframe="now 7-d",
                        geo="US",
                    )
                    related = pytrends.related_queries()
                    rising = related.get(category, {}).get("rising")
                    if rising is None or rising.empty:
                        continue

                    for _, row in rising.head(3).iterrows():
                        query = str(row["query"])
                        value = int(row["value"])
                        products.append(ScrapedProduct(
                            title=query.title(),
                            source="google_trends",
                            source_product_id=query.lower().replace(" ", "_"),
                            description=f"Trending search: '{query}' — breakout {value}%+ increase",
                            category=category,
                            tags=["trending", category.replace(" ", "-")],
                            views=value * 100,  # relative popularity proxy
                            raw_data={
                                "query": query,
                                "value": value,
                                "category": category,
                                "timeframe": "7d",
                            },
                        ))
                        if len(products) >= limit:
                            return products
                except Exception as e:
                    logger.warning("google_trends_category_failed", category=category, error=str(e))
        except Exception as e:
            logger.error("google_trends_scraper_failed", error=str(e))
        return products
