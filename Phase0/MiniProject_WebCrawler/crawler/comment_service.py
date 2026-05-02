"""
Comment service: lấy comment qua API trong browser context.
Nếu API fail → trả list rỗng, không crash pipeline.
"""

from config import COMMENT_API_URL, MAX_COMMENTS_PER_PRODUCT
from crawler.fetcher import Fetcher
from storage.models import Comment
from utils import setup_logging

logger = setup_logging("comment_service")


class CommentService:
    """Lấy comment/review qua Chiaki API (từ browser context)."""

    def __init__(self, fetcher: Fetcher):
        self.fetcher = fetcher

    def fetch_comments(
        self, product_id: int, max_comments: int = MAX_COMMENTS_PER_PRODUCT
    ) -> list[Comment]:
        """Gọi API load_comment từ browser context (bypass CORS/auth)."""

        api_url = (
            f"{COMMENT_API_URL}"
            f"?embeds=replies"
            f"&fields=id,user,content,evaluation,create_time"
            f"&filters=target_id%3D{product_id},"
            f"is_qa%3D0,"
            f"type%3D%7Bproduct%2Creview_order%7D,"
            f"status%3Dactive,"
            f"content!%3Dnull"
            f"&page_id=1"
            f"&page_size={max_comments}"
            f"&sorts=-create_time,-evaluation,-like_count"
        )

        data = self.fetcher.fetch_api_from_page(api_url)

        if not data:
            logger.warning(f"No comment data for product {product_id} (API may have denied)")
            return []

        return self._parse_comments(data, product_id)

    def _parse_comments(self, data: dict, product_id: int) -> list[Comment]:
        """Parse API response → list[Comment]."""
        comments = []
        items = data.get("data", [])

        if not isinstance(items, list):
            return []

        for item in items:
            content = (item.get("content") or "").strip()
            if not content or len(content) < 3:
                continue

            comment = Comment(
                comment_id=item.get("id", 0),
                product_id=product_id,
                user=item.get("user", ""),
                content=content,
                evaluation=item.get("evaluation", 0),
                created_at=item.get("create_time", ""),
            )
            comments.append(comment)

        return comments
