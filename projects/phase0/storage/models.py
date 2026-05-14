"""
Data models: Product và Comment.
"""

from dataclasses import dataclass, field


@dataclass
class Comment:
    comment_id: int
    product_id: int
    user: str
    content: str
    evaluation: int
    created_at: str


@dataclass
class Product:
    product_id: int
    url: str
    name: str
    description_short: str
    description_long: str
    category: str
    crawled_at: str
    comments: list[Comment] = field(default_factory=list)
    price: str = ""
    images: list[str] = field(default_factory=list)
    rating_count: int = 0
    metadata: dict = field(default_factory=dict)
