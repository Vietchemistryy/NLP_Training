"""
Comment service: quyết định khi nào cần Playwright; fallback 3 lớp.
1) requests (static)
2) [API_INTERCEPT] Playwright listen XHR/Fetch
3) XHR evaluate trong page (dynamic fetcher)
4) [PARSE] DOM extraction
5) empty + warning — không crash pipeline
"""

from __future__ import annotations

import random
from urllib.parse import urlencode

from config import (
    COMMENT_API_URL,
    CRAWL_COMMENTS_RATIO,
    MAX_COMMENTS_PER_PRODUCT,
)
from crawler.dynamic_fetcher import DynamicFetcher
from crawler.parser import ProductPayload, parse_reviews_from_dom
from crawler.static_fetcher import StaticFetcher
from storage.models import Comment
from utils import setup_logging

logger = setup_logging("comment_service")


def should_crawl_comments(payload: ProductPayload | None) -> bool:
    """Crawl comment nếu rating_count > 0 hoặc random theo CRAWL_COMMENTS_RATIO."""
    if not payload:
        return False
    rc = int(payload.get("rating_count") or 0)
    if rc > 0:
        return True
    return random.random() < float(CRAWL_COMMENTS_RATIO)


class CommentService:
    def __init__(self, static_fetcher: StaticFetcher, dynamic_fetcher: DynamicFetcher) -> None:
        self.static_fetcher = static_fetcher
        self.dynamic_fetcher = dynamic_fetcher

    def build_comment_api_url(self, product_id: int, max_comments: int) -> str:
        filters = (
            f"target_id={product_id},"
            "is_qa=0,"
            "type={product;review_order},"
            "status=active,"
            "content!=null"
        )
        params = urlencode(
            {
                "embeds": "replies",
                "fields": "id,user,content,evaluation,create_time",
                "filters": filters,
                "page_id": 1,
                "page_size": max_comments,
                "sorts": "-create_time,-evaluation,-like_count",
            }
        )
        return f"{COMMENT_API_URL}?{params}"

    def fetch_comments(
        self,
        product_id: int,
        product_url: str,
        product_payload: ProductPayload | None = None,
        max_comments: int = MAX_COMMENTS_PER_PRODUCT,
        force_dynamic: bool = False,
    ) -> list[Comment]:
        if not product_id:
            logger.warning("[PARSE] fetch_comments: empty product_id — skip")
            return []

        if product_payload is not None and not should_crawl_comments(product_payload):
            logger.info(
                f"[STATIC] Skip comments (rating_count={product_payload.get('rating_count', 0)}, "
                f"ratio gate)"
            )
            return []

        api_url = self.build_comment_api_url(product_id, max_comments)
        referer_headers = {
            "Accept": "application/json",
            "Referer": product_url,
        }

        data: dict | None = None

        # Tier 1: static requests
        if not force_dynamic:
            logger.info(f"[STATIC] Fetching comments API for product_id={product_id}")
            response = self.static_fetcher.get(api_url, headers=referer_headers)
            if response and response.status_code == 200:
                try:
                    data = response.json()
                except ValueError:
                    data = None
            if data and isinstance(data, dict) and data.get("status") != "fail":
                return self._parse_comments(data, product_id)

        # Tier 2: API intercept on real product page
        logger.info(f"[API_INTERCEPT] Trying Playwright intercept for product_id={product_id}")
        try:
            intercepted = self.dynamic_fetcher.collect_comment_api_via_intercept(product_url)
            if intercepted and isinstance(intercepted, dict) and intercepted.get("status") != "fail":
                data = intercepted
                cookies = self.dynamic_fetcher.get_cookies()
                if cookies:
                    self.static_fetcher.update_cookies(cookies)
                return self._parse_comments(data, product_id)
        except Exception as e:
            logger.warning(f"[API_INTERCEPT] Intercept failed: {e}")

        # Tier 3a: XHR in page
        logger.info(f"[DYNAMIC] Fallback XHR evaluate for product_id={product_id}")
        data = self.dynamic_fetcher.fetch_api_from_page(api_url, context_url=product_url)
        if data and isinstance(data, dict) and data.get("status") != "fail":
            cookies = self.dynamic_fetcher.get_cookies()
            if cookies:
                self.static_fetcher.update_cookies(cookies)
            return self._parse_comments(data, product_id)

        # Tier 3b: DOM
        if self.dynamic_fetcher.navigate(product_url):
            page = self.dynamic_fetcher.page
            if page:
                raw_items = parse_reviews_from_dom(page)
                if raw_items:
                    comments: list[Comment] = []
                    for item in raw_items:
                        content = (item.get("content") or "").strip()
                        if len(content) < 3:
                            continue
                        comments.append(
                            Comment(
                                comment_id=int(item.get("id", 0)),
                                product_id=product_id,
                                user=str(item.get("user") or "Ẩn danh"),
                                content=content[:5000],
                                evaluation=int(item.get("evaluation") or 0),
                                created_at=str(item.get("create_time") or ""),
                            )
                        )
                    if comments:
                        logger.info(f"[PARSE] DOM fallback → {len(comments)} comments")
                        return comments

        logger.warning(
            f"[PARSE] No comments for product_id={product_id} — all tiers exhausted (empty)"
        )
        return []

    def _parse_comments(self, data: dict, product_id: int) -> list[Comment]:
        comments: list[Comment] = []
        items = data.get("data") or data.get("result") or []
        if not isinstance(items, list):
            logger.warning(f"[PARSE] Unexpected 'data'/'result' type for product {product_id}: {type(items).__name__}")
            return []

        for item in items:
            content = (item.get("content") or "").strip()
            if not content or len(content) < 3:
                continue
            comments.append(
                Comment(
                    comment_id=item.get("id", 0),
                    product_id=product_id,
                    user=self._extract_user(item.get("user")),
                    content=content,
                    evaluation=item.get("evaluation", 0),
                    created_at=item.get("create_time", ""),
                )
            )
        logger.info(f"[PARSE] Parsed {len(comments)} comments for product {product_id}")
        return comments

    @staticmethod
    def _extract_user(user_raw: object) -> str:
        if user_raw is None:
            return "Ẩn danh"
        if isinstance(user_raw, dict):
            return (
                user_raw.get("name")
                or user_raw.get("full_name")
                or user_raw.get("username")
                or "Ẩn danh"
            )
        return str(user_raw).strip() or "Ẩn danh"
