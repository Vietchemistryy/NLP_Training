"""
Data models: Product và Comment.
Dùng dataclass — lightweight, immutable-friendly.
"""

from dataclasses import dataclass, field


@dataclass
class Comment:
    """Một comment/review của sản phẩm."""
    comment_id: int
    product_id: int
    user: str
    content: str
    evaluation: int  # rating 1-5
    created_at: str


@dataclass
class Product:
    """Thông tin sản phẩm đã crawl."""
    product_id: int
    url: str
    name: str
    description_short: str
    description_long: str
    category: str
    crawled_at: str
    comments: list[Comment] = field(default_factory=list)
