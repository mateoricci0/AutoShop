from playwright.async_api import async_playwright, Browser, BrowserContext
import asyncio
from contextlib import asynccontextmanager
import structlog

logger = structlog.get_logger()


class PlaywrightPool:
    """Manages a pool of Playwright browser instances."""

    def __init__(self, max_browsers: int = 3):
        self._semaphore = asyncio.Semaphore(max_browsers)
        self._playwright = None
        self._browser: Browser | None = None

    async def start(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
            ],
        )
        logger.info("playwright_pool_started")

    async def stop(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("playwright_pool_stopped")

    @asynccontextmanager
    async def acquire_context(self, **context_kwargs):
        """Get a browser context from the pool."""
        async with self._semaphore:
            ctx = await self._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 720},
                **context_kwargs,
            )
            try:
                yield ctx
            finally:
                await ctx.close()


# Global pool instance — initialized in FastAPI lifespan
_pool: PlaywrightPool | None = None


def get_pool() -> PlaywrightPool:
    if _pool is None:
        raise RuntimeError("Playwright pool not initialized")
    return _pool


async def init_pool(max_browsers: int = 3) -> PlaywrightPool:
    global _pool
    _pool = PlaywrightPool(max_browsers)
    await _pool.start()
    return _pool


async def shutdown_pool():
    global _pool
    if _pool:
        await _pool.stop()
        _pool = None
