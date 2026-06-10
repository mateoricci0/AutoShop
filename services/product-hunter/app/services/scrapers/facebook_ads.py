import httpx
from .base import BaseScraper, ScrapedProduct, ScraperUnavailable
import structlog
import asyncio

logger = structlog.get_logger()

SEARCH_QUERIES = [
    "buy now", "limited offer", "shop now", "order today",
    "free shipping", "50% off",
]


class FacebookAdsScraper(BaseScraper):
    name = "facebook_ads"

    def __init__(self, apify_api_key: str = ""):
        self.apify_api_key = apify_api_key

    async def scrape(self, limit: int = 20) -> list[ScrapedProduct]:
        if self.apify_api_key:
            return await self._scrape_via_apify(limit)
        return await self._scrape_fallback(limit)

    async def _scrape_via_apify(self, limit: int) -> list[ScrapedProduct]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.apify.com/v2/acts/apify~facebook-ads-scraper/runs",
                headers={"Authorization": f"Bearer {self.apify_api_key}"},
                json={"searchTerms": SEARCH_QUERIES[:3], "maxResults": limit},
            )
            if resp.status_code not in (200, 201):
                return await self._scrape_fallback(limit)

            run_id = resp.json()["data"]["id"]
            for _ in range(12):
                await asyncio.sleep(5)
                s = await client.get(
                    f"https://api.apify.com/v2/runs/{run_id}",
                    headers={"Authorization": f"Bearer {self.apify_api_key}"},
                )
                if s.json()["data"]["status"] == "SUCCEEDED":
                    break

            items_resp = await client.get(
                f"https://api.apify.com/v2/runs/{run_id}/dataset/items",
                headers={"Authorization": f"Bearer {self.apify_api_key}"},
            )

            products = []
            for item in items_resp.json()[:limit]:
                title = item.get("title") or item.get("pageName") or "Facebook Ad Product"
                products.append(ScrapedProduct(
                    title=str(title)[:255],
                    source="facebook_ads",
                    source_product_id=item.get("adArchiveId", ""),
                    source_url=item.get("snapshot", {}).get("link_url"),
                    description=item.get("snapshot", {}).get("body", {}).get("text", ""),
                    images=[{"url": item.get("snapshot", {}).get("images", [{}])[0].get("original_image_url", ""), "alt": str(title)}],
                    tags=["facebook", "paid-ad"],
                    raw_data=item,
                ))
            return products

    async def _scrape_fallback(self, limit: int) -> list[ScrapedProduct]:
        """Fallback: return empty (Facebook Ad Library requires JS rendering)."""
        logger.info("facebook_ads_skipped_no_apify_key")
        return []
