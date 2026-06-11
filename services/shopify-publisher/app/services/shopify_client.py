"""Async Shopify Admin REST API client with leaky-bucket rate limiter.

Shopify allows ~40 req/s for Plus stores and ~2 req/s for Basic.
We default to 2 req/s (1 token per 500 ms) which is safe for all plan types.
Each store gets its own rate limiter keyed by store domain.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

_limiters: dict[str, "LeakyBucket"] = {}


class LeakyBucket:
    """Token-bucket rate limiter — `rate` tokens per second."""

    def __init__(self, rate: float = 2.0) -> None:
        self._rate = rate
        self._tokens = rate
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self._rate, self._tokens + elapsed * self._rate)
            self._last_refill = now
            if self._tokens < 1:
                wait = (1 - self._tokens) / self._rate
                await asyncio.sleep(wait)
                self._tokens = 0
            else:
                self._tokens -= 1


def _get_limiter(domain: str) -> LeakyBucket:
    if domain not in _limiters:
        _limiters[domain] = LeakyBucket(rate=2.0)
    return _limiters[domain]


class ShopifyClient:
    """Async wrapper around Shopify Admin REST API 2024-10."""

    def __init__(self, domain: str, access_token: str, api_version: str = "2024-10") -> None:
        self._domain = domain
        self._base = f"https://{domain}/admin/api/{api_version}"
        self._headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }
        self._limiter = _get_limiter(domain)

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        await self._limiter.acquire()
        url = f"{self._base}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(method, url, headers=self._headers, **kwargs)
        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", "2"))
            logger.warning("shopify_rate_limited", domain=self._domain, retry_after=retry_after)
            await asyncio.sleep(retry_after)
            return await self._request(method, path, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    # ── Products ──────────────────────────────────────────────────────────────

    async def create_product(self, payload: dict) -> dict:
        data = await self._request("POST", "/products.json", json={"product": payload})
        return data["product"]

    async def update_product(self, product_id: str, payload: dict) -> dict:
        data = await self._request(
            "PUT", f"/products/{product_id}.json", json={"product": payload}
        )
        return data["product"]

    async def archive_product(self, product_id: str) -> dict:
        return await self.update_product(product_id, {"status": "archived"})

    async def get_product(self, product_id: str) -> dict:
        data = await self._request("GET", f"/products/{product_id}.json")
        return data["product"]

    # ── Images ────────────────────────────────────────────────────────────────

    async def add_product_image(self, product_id: str, src: str, alt: str = "") -> dict:
        data = await self._request(
            "POST",
            f"/products/{product_id}/images.json",
            json={"image": {"src": src, "alt": alt}},
        )
        return data["image"]

    # ── Collections ───────────────────────────────────────────────────────────

    async def list_custom_collections(self) -> list[dict]:
        data = await self._request("GET", "/custom_collections.json?limit=250")
        return data.get("custom_collections", [])

    async def create_custom_collection(self, title: str) -> dict:
        data = await self._request(
            "POST",
            "/custom_collections.json",
            json={"custom_collection": {"title": title}},
        )
        return data["custom_collection"]

    async def add_collect(self, product_id: str, collection_id: str) -> dict:
        data = await self._request(
            "POST",
            "/collects.json",
            json={"collect": {"product_id": product_id, "collection_id": collection_id}},
        )
        return data.get("collect", {})

    # ── Metafields (SEO) ──────────────────────────────────────────────────────

    async def set_product_metafields(self, product_id: str, metafields: list[dict]) -> None:
        for mf in metafields:
            await self._request(
                "POST",
                f"/products/{product_id}/metafields.json",
                json={"metafield": mf},
            )

    # ── Shop info ─────────────────────────────────────────────────────────────

    async def get_shop(self) -> dict:
        data = await self._request("GET", "/shop.json")
        return data["shop"]
