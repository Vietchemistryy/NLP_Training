"""
Parser: tách parse static (BeautifulSoup) và helper parse dynamic (DOM / Playwright page).
Trả về ProductPayload dict thống nhất; chuyển sang Product qua product_dict_to_product().
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, TypedDict

from bs4 import BeautifulSoup
from playwright.sync_api import Page

from crawler.static_fetcher import StaticFetcher
from storage.models import Product
from utils import clean_text, extract_product_id, setup_logging

logger = setup_logging("parser")


class ProductPayload(TypedDict, total=False):
    """Cấu trúc dict thống nhất cho 1 sản phẩm (static + metadata cho comment gate)."""

    product_id: int
    url: str
    category: str
    title: str
    price: str
    images: list[str]
    description: str
    description_short: str
    description_long: str
    comments: list[dict[str, Any]]
    rating_count: int
    metadata: dict[str, Any]


def parse_product_list_static(html: str, category_url: str) -> list[dict[str, str]]:
    """[PARSE] Danh sách link sản phẩm từ HTML category (static)."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict[str, str]] = []
    seen: set[str] = set()

    for a in soup.select('a[href*="chiaki.vn/"], a.product-item-link, a[class*="product-item"]'):
        href = (a.get("href") or "").strip()
        if not href or "chiaki.vn" not in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        name = (a.get("title") or a.get_text() or "").strip()
        if name and len(name) > 3:
            results.append({"url": href, "name": name[:200]})

    if not results:
        logger.debug(f"[PARSE] No product links via primary selectors: {category_url}")
    return results


def _extract_price(soup: BeautifulSoup) -> str:
    candidates = (
        soup.select_one("[class*='price'] [class*='current']"),
        soup.select_one("[class*='product-price']"),
        soup.select_one("[data-price]"),
        soup.select_one(".price"),
    )
    for el in candidates:
        if el:
            t = clean_text(el.get_text())
            if t and re.search(r"\d", t):
                return t[:120]
    for s in soup.find_all("script", type="application/ld+json"):
        raw = s.string or ""
        if "price" in raw.lower():
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    offers = data.get("offers")
                    if isinstance(offers, dict) and offers.get("price"):
                        return str(offers["price"])
            except (json.JSONDecodeError, TypeError):
                continue
    return ""


def _extract_images(soup: BeautifulSoup, base_host: str = "https://chiaki.vn") -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for img in soup.select(
        '.product-gallery img[src], [class*="product"] img[src], meta[property="og:image"][content]'
    ):
        src = (img.get("src") or img.get("content") or "").strip()
        if not src or src.startswith("data:"):
            continue
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = base_host.rstrip("/") + src
        ok = (src not in seen) and ("chiaki" in src or src.startswith("http"))
        if ok:
            seen.add(src)
            urls.append(src)
    return urls[:30]


def _extract_rating_count(soup: BeautifulSoup) -> int:
    text = soup.get_text(" ", strip=True)
    m = re.search(r"(\d+)\s*(đánh giá|review|reviews|rating)", text, re.I)
    if m:
        return int(m.group(1))
    for el in soup.select("[class*='review'], [class*='rating'], [data-review-count]"):
        val = el.get("data-review-count") or el.get("data-count")
        if val and str(val).isdigit():
            return int(val)
    return 0


def parse_product_detail_static(html: str, url: str, category: str) -> ProductPayload | None:
    """[PARSE] Chi tiết sản phẩm từ HTML (BeautifulSoup). comments luôn []."""
    soup = BeautifulSoup(html, "html.parser")

    pid = extract_product_id(url)
    if pid is None:
        for s in soup.find_all("script"):
            text = s.string or ""
            if "productData" in text or '"id"' in text:
                m = re.search(r'"id"\s*:\s*(\d+)', text)
                if m:
                    pid = int(m.group(1))
                    break
    if pid is None:
        pid = abs(hash(url)) % (10**9)

    h1 = soup.find("h1")
    title = clean_text(h1.get_text()) if h1 else ""
    if not title:
        logger.warning(f"[PARSE] Missing title: {url}")
        return None

    desc_short = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        desc_short = clean_text(meta_desc.get("content", ""))

    desc_long = ""
    content_box = soup.select_one(
        '.product-contentbox, .product-content, [class*="product-detail"], [class*="description"]'
    )
    if content_box:
        desc_long = clean_text(content_box.get_text(separator=" ", strip=True))

    description = desc_long or desc_short
    price = _extract_price(soup)
    images = _extract_images(soup)
    rating_count = _extract_rating_count(soup)

    payload: ProductPayload = {
        "product_id": pid,
        "url": url,
        "category": category,
        "title": title,
        "price": price,
        "images": images,
        "description": description,
        "description_short": desc_short,
        "description_long": desc_long,
        "comments": [],
        "rating_count": rating_count,
        "metadata": {"source": "static_html"},
    }
    return payload


def parse_reviews_from_dom(page: Page) -> list[dict[str, Any]]:
    """[PARSE] Fallback tier 3: trích review từ DOM sau khi JS render."""
    try:
        items = page.evaluate(
            """() => {
                const out = [];
                const nodes = document.querySelectorAll(
                  '[class*="comment"], [class*="review"], [data-testid*="review"], article[class*="item"]'
                );
                nodes.forEach((n, i) => {
                  const text = (n.innerText || '').trim();
                  if (text.length < 5) return;
                  out.push({
                    idx: i,
                    content: text.slice(0, 2000),
                    raw_html_len: n.innerHTML ? n.innerHTML.length : 0
                  });
                });
                return out;
            }"""
        )
    except Exception as e:
        logger.warning(f"[PARSE] DOM review extraction failed: {e}")
        return []

    if not items:
        logger.warning("[PARSE] DOM review extraction returned no blocks")
        return []

    result: list[dict[str, Any]] = []
    for i, it in enumerate(items):
        content = (it.get("content") or "").strip()
        if len(content) < 3:
            continue
        cid = abs(hash((content[:200], i))) % (2**31 - 1) or (i + 1)
        result.append(
            {
                "id": cid,
                "content": content,
                "evaluation": 0,
                "create_time": "",
                "user": "DOM",
            }
        )
    logger.info(f"[PARSE] DOM fallback extracted {len(result)} review-like blocks")
    return result


def product_dict_to_product(payload: ProductPayload, crawled_at: str | None = None) -> Product:
    """Map ProductPayload → Product (storage)."""
    when = crawled_at or datetime.now(timezone.utc).isoformat()
    meta = dict(payload.get("metadata") or {})
    meta.setdefault("price", payload.get("price", ""))
    meta.setdefault("images", payload.get("images", []))
    meta.setdefault("rating_count", payload.get("rating_count", 0))

    return Product(
        product_id=payload["product_id"],
        url=payload["url"],
        name=payload["title"],
        description_short=payload.get("description_short") or "",
        description_long=payload.get("description_long") or payload.get("description") or "",
        category=payload.get("category") or "",
        crawled_at=when,
        price=payload.get("price") or "",
        images=list(payload.get("images") or []),
        rating_count=int(payload.get("rating_count") or 0),
        metadata=meta,
    )


class ProductParser:
    """Facade: fetch + parse static — tương thích main."""

    def __init__(self, fetcher: StaticFetcher) -> None:
        self.fetcher = fetcher

    def fetch_product_list(self, category_url: str) -> list[dict]:
        html = self.fetcher.get_html(category_url)
        if not html:
            logger.warning(f"[PARSE] Failed to fetch category HTML: {category_url}")
            return []
        return parse_product_list_static(html, category_url)

    def fetch_product_detail(self, url: str, category: str) -> Product | None:
        payload = self.fetch_product_detail_payload(url, category)
        if not payload:
            return None
        return product_dict_to_product(payload)

    def fetch_product_detail_payload(self, url: str, category: str) -> ProductPayload | None:
        """Dict thống nhất (cho CommentService gate + metadata)."""
        html = self.fetcher.get_html(url)
        if not html:
            logger.warning(f"[PARSE] Failed to fetch product HTML: {url}")
            return None
        return parse_product_detail_static(html, url, category)
