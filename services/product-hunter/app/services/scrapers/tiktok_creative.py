import httpx
from .base import BaseScraper, ScrapedProduct, ScraperUnavailable
from ..scrapers.playwright_base import get_pool
import structlog
import asyncio

logger = structlog.get_logger()


class TikTokCreativeScraper(BaseScraper):
    name = "tiktok_creative"
    requires_playwright = True

    def __init__(self, apify_api_key: str = ""):
        self.apify_api_key = apify_api_key

    async def scrape(self, limit: int = 20) -> list[ScrapedProduct]:
        if self.apify_api_key:
            return await self._scrape_via_apify(limit)
        return await self._scrape_via_playwright(limit)

    async def _scrape_via_apify(self, limit: int) -> list[ScrapedProduct]:
        """Use Apify's TikTok Creative Center scraper actor."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Start actor run
            resp = await client.post(
                "https://api.apify.com/v2/acts/clockworks~tiktok-creative-center-ads/runs",
                headers={"Authorization": f"Bearer {self.apify_api_key}"},
                json={
                    "limit": limit,
                    "region": "US",
                    "sortBy": "like",
                    "period": "7",
                },
            )
            if resp.status_code not in (200, 201):
                logger.warning("apify_run_failed", status=resp.status_code)
                return []

            run_id = resp.json()["data"]["id"]

            # Wait for completion (poll every 5s, max 60s)
            for _ in range(12):
                await asyncio.sleep(5)
                status_resp = await client.get(
                    f"https://api.apify.com/v2/acts/clockworks~tiktok-creative-center-ads/runs/{run_id}",
                    headers={"Authorization": f"Bearer {self.apify_api_key}"},
                )
                if status_resp.json()["data"]["status"] == "SUCCEEDED":
                    break

            # Fetch results
            items_resp = await client.get(
                f"https://api.apify.com/v2/acts/clockworks~tiktok-creative-center-ads/runs/{run_id}/dataset/items",
                headers={"Authorization": f"Bearer {self.apify_api_key}"},
            )

            products = []
            for item in items_resp.json()[:limit]:
                products.append(ScrapedProduct(
                    title=item.get("title", item.get("desc", "TikTok Ad"))[:255],
                    source="tiktok_creative",
                    source_product_id=item.get("id", ""),
                    source_url=item.get("videoUrl"),
                    description=item.get("desc"),
                    images=[{"url": item.get("cover", ""), "alt": "TikTok ad"}],
                    likes=item.get("likeCount"),
                    comments=item.get("commentCount"),
                    shares=item.get("shareCount"),
                    views=item.get("playCount"),
                    raw_data=item,
                ))
            return products

    async def _scrape_via_playwright(self, limit: int) -> list[ScrapedProduct]:
        """Direct Playwright scrape of TikTok Creative Center."""
        try:
            pool = get_pool()
        except RuntimeError:
            raise ScraperUnavailable("Playwright pool not initialized")

        products = []
        async with pool.acquire_context() as ctx:
            page = await ctx.new_page()
            try:
                await page.goto(
                    "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en",
                    wait_until="networkidle",
                    timeout=30000,
                )
                await page.wait_for_selector("[class*='topAdsCard'], [class*='card-container']", timeout=15000)

                cards = await page.query_selector_all("[class*='topAdsCard'], [class*='card-container']")

                for card in cards[:limit]:
                    try:
                        title_el = await card.query_selector("[class*='title'], h3")
                        title = await title_el.inner_text() if title_el else "TikTok Product"

                        img_el = await card.query_selector("img")
                        img_url = await img_el.get_attribute("src") if img_el else ""

                        likes_el = await card.query_selector("[class*='like'], [class*='stat']")
                        likes_text = await likes_el.inner_text() if likes_el else ""

                        products.append(ScrapedProduct(
                            title=title.strip()[:255],
                            source="tiktok_creative",
                            source_product_id=title.lower()[:50],
                            images=[{"url": img_url, "alt": title}] if img_url else [],
                            tags=["tiktok", "viral"],
                            raw_data={"likes_text": likes_text},
                        ))
                    except Exception as e:
                        logger.debug("tiktok_card_error", error=str(e))
            except Exception as e:
                logger.warning("tiktok_playwright_failed", error=str(e))
            finally:
                await page.close()

        return products
