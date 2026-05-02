"""
Parser: extract product data từ rendered DOM (Playwright).
Chiaki.vn là SPA — product listing dùng a.product-item-link,
pagination dùng "Xem thêm" button hoặc ?page=N.
"""

import re
from datetime import datetime, timezone

from crawler.fetcher import Fetcher
from storage.models import Product
from utils import clean_text, setup_logging

logger = setup_logging("parser")


class ProductParser:
    """Extract product data từ chiaki.vn rendered pages."""

    def __init__(self, fetcher: Fetcher):
        self.fetcher = fetcher

    def fetch_product_list(self, category_url: str) -> list[dict]:
        """Navigate tới category page, click 'Xem thêm' nhiều lần để load hết,
        rồi extract tất cả product URLs.

        Returns: [{"url": ..., "name": ...}, ...]
        """
        # Navigate tới category page
        initial = self.fetcher.evaluate_on_page(category_url, """
            () => document.querySelectorAll('a.product-item-link').length
        """)

        if initial is None:
            return []

        # Click "Xem thêm" tối đa 10 lần để load thêm sản phẩm
        self.fetcher.evaluate_on_page(None, """
            async () => {
                for (let i = 0; i < 10; i++) {
                    const buttons = Array.from(document.querySelectorAll('button, a, span, div'));
                    const loadMore = buttons.find(el => {
                        const text = el.textContent.trim().toLowerCase();
                        return text === 'xem thêm' || text === 'xem thêm sản phẩm' || text.includes('load more');
                    });
                    if (!loadMore) break;
                    loadMore.click();
                    await new Promise(r => setTimeout(r, 2000));
                }
            }
        """)

        # Extract all products after loading
        products = self.fetcher.evaluate_on_page(None, """
            () => {
                const results = [];
                const seen = new Set();

                document.querySelectorAll('a.product-item-link, a[class*="product-item"]').forEach(a => {
                    const href = a.href;
                    if (href && href.includes('chiaki.vn/') && !seen.has(href)) {
                        seen.add(href);
                        const name = (a.getAttribute('title') || a.textContent || '').trim();
                        if (name && name.length > 3) {
                            results.push({url: href, name: name.substring(0, 200)});
                        }
                    }
                });

                return results;
            }
        """)

        return products or []

    def fetch_product_detail(self, url: str, category: str) -> Product | None:
        """Navigate tới product page → extract details từ rendered DOM."""
        data = self.fetcher.evaluate_on_page(url, """
            () => {
                // Get product ID
                let productId = null;

                // Try URL pattern (some URLs end with -DIGITS)
                const urlMatch = window.location.href.match(/-(\\d+)$/);
                if (urlMatch) productId = parseInt(urlMatch[1]);

                // Try productData JS var
                try {
                    if (typeof productData !== 'undefined' && productData.id) {
                        productId = productData.id;
                    }
                } catch(e) {}

                // Try scripts
                if (!productId) {
                    for (const s of document.querySelectorAll('script')) {
                        const text = s.textContent || '';
                        const match = text.match(/"id"\\s*:\\s*(\\d+)/);
                        if (match && text.includes('productData')) {
                            productId = parseInt(match[1]);
                            break;
                        }
                    }
                }

                // Name
                const h1 = document.querySelector('h1');
                const name = h1 ? h1.textContent.trim() : '';

                // Short description
                let descShort = '';
                const metaDesc = document.querySelector('meta[name="description"]');
                if (metaDesc) descShort = metaDesc.content || '';

                // Long description
                let descLong = '';
                const contentBox = document.querySelector('.product-contentbox, .product-content');
                if (contentBox) descLong = contentBox.innerText || '';

                return {productId, name, descShort, descLong, url: window.location.href};
            }
        """)

        if not data or not data.get("name"):
            logger.warning(f"Cannot parse product: {url}")
            return None

        product_id = data.get("productId")
        if not product_id:
            # Fallback: use hash of URL
            product_id = abs(hash(url)) % (10 ** 9)

        return Product(
            product_id=product_id,
            url=data.get("url", url),
            name=clean_text(data["name"]),
            description_short=clean_text(data.get("descShort", "")),
            description_long=clean_text(data.get("descLong", "")),
            category=category,
            crawled_at=datetime.now(timezone.utc).isoformat(),
        )
