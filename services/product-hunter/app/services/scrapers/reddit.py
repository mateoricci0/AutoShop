import httpx
from .base import BaseScraper, ScrapedProduct, ScraperUnavailable
import structlog
import re

logger = structlog.get_logger()

SUBREDDITS = [
    "amazonfinds", "BuyItForLife", "malegrooming", "femalefashionadvice",
    "HomeImprovement", "shutupandtakemymoney", "gadgets", "fitness",
]


class RedditScraper(BaseScraper):
    name = "reddit"
    HEADERS = {
        "User-Agent": "ASE-ProductHunter/1.0 (product research tool)",
        "Accept": "application/json",
    }

    async def scrape(self, limit: int = 20) -> list[ScrapedProduct]:
        products = []
        per_sub = max(3, limit // len(SUBREDDITS))

        async with httpx.AsyncClient(
            headers=self.HEADERS,
            timeout=15.0,
            follow_redirects=True,
        ) as client:
            for subreddit in SUBREDDITS:
                if len(products) >= limit:
                    break
                try:
                    resp = await client.get(
                        f"https://www.reddit.com/r/{subreddit}/hot.json",
                        params={"limit": per_sub * 2},
                    )
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    posts = data.get("data", {}).get("children", [])

                    for post in posts:
                        p = post.get("data", {})
                        # Filter: min 50 upvotes, min 0.7 ratio, not pinned
                        if (
                            p.get("score", 0) < 50
                            or p.get("upvote_ratio", 0) < 0.70
                            or p.get("stickied")
                            or p.get("is_self") and len(p.get("selftext", "")) < 50
                        ):
                            continue

                        title = p.get("title", "").strip()
                        if len(title) < 10:
                            continue

                        products.append(ScrapedProduct(
                            title=title[:255],
                            source="reddit",
                            source_product_id=p.get("id"),
                            source_url=f"https://reddit.com{p.get('permalink', '')}",
                            description=p.get("selftext", "")[:500] or p.get("url", ""),
                            category=subreddit,
                            tags=[subreddit, "reddit"],
                            likes=p.get("score"),
                            comments=p.get("num_comments"),
                            images=[{"url": p["url"], "alt": title}] if p.get("url", "").endswith((".jpg", ".png", ".webp")) else [],
                            raw_data={
                                "subreddit": subreddit,
                                "score": p.get("score"),
                                "upvote_ratio": p.get("upvote_ratio"),
                                "num_comments": p.get("num_comments"),
                                "url": p.get("url"),
                                "created_utc": p.get("created_utc"),
                            },
                        ))

                        if len(products) >= limit:
                            break
                except Exception as e:
                    logger.warning("reddit_subreddit_failed", subreddit=subreddit, error=str(e))

        return products
