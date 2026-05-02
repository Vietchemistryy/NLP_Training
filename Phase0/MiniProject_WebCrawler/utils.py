"""
Utility functions: text cleaning, ID extraction, logging.
Functional — không dùng class.
"""

import logging
import re


def setup_logging(name: str = "webcrawler") -> logging.Logger:
    """Configure logger với format chuẩn."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def clean_text(text: str) -> str:
    """Strip HTML tags, {{template}} vars, normalize whitespace."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove {{template}} placeholders
    text = re.sub(r"\{\{.*?\}\}", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_product_id(url: str) -> int | None:
    """Extract numeric ID ở cuối URL chiaki.vn.

    Ví dụ: 'https://chiaki.vn/men-vi-sinh-bifina-baby-203451' → 203451
    """
    match = re.search(r"-(\d+)$", url.rstrip("/"))
    if match:
        return int(match.group(1))
    return None
