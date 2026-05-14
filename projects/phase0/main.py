"""
CLI entrypoint: crawl hoặc serve

Hybrid orchestration:
- StaticFetcher: danh sách + chi tiết HTML (requests).
- ProductParser: ProductPayload dict → Product.
- CommentService: gate theo rating_count + CRAWL_COMMENTS_RATIO; 3-tier comments.
- DynamicFetcher: đóng trong finally để tránh memory leak.

Usage:
    python main.py crawl
    python main.py serve
"""

from __future__ import annotations

import os
import sys
import traceback

from config import CATEGORIES, DATA_DIR, DB_PATH, JSON_PATH, MAX_PRODUCTS_TOTAL
from crawler.comment_service import CommentService
from crawler.dynamic_fetcher import DynamicFetcher
from crawler.parser import ProductParser, product_dict_to_product
from crawler.static_fetcher import StaticFetcher
from storage.repository import ProductRepository
from utils import setup_logging

logger = setup_logging("main")


def crawl() -> None:
    logger.info("=" * 60)
    logger.info("Starting hybrid crawl (static + dynamic on demand)...")
    logger.info(f"Target: {len(CATEGORIES)} categories, max {MAX_PRODUCTS_TOTAL} products")
    logger.info("=" * 60)

    os.makedirs(DATA_DIR, exist_ok=True)

    static_fetcher = StaticFetcher()
    dynamic_fetcher = DynamicFetcher()
    ua = static_fetcher.session.headers.get("User-Agent", "")
    if ua:
        dynamic_fetcher.align_user_agent_with_static(ua)

    parser = ProductParser(static_fetcher)
    comment_service = CommentService(static_fetcher, dynamic_fetcher)
    repo = ProductRepository(DB_PATH)

    total_crawled = 0
    total_comments = 0
    failed = 0

    try:
        for category_name, _category_id in CATEGORIES:
            if total_crawled >= MAX_PRODUCTS_TOTAL:
                break

            category_url = f"https://chiaki.vn/{category_name}"
            logger.info(f"\n--- Category: {category_name} ---")

            product_links = parser.fetch_product_list(category_url)
            if not product_links:
                logger.info("  No products found")
                continue

            logger.info(f"  Found {len(product_links)} products in category")

            for link_data in product_links:
                if total_crawled >= MAX_PRODUCTS_TOTAL:
                    break

                product_url = link_data["url"]
                if not product_url.startswith("http"):
                    product_url = "https://chiaki.vn" + (
                        product_url if product_url.startswith("/") else "/" + product_url
                    )

                if repo.url_exists(product_url):
                    continue

                try:
                    payload = parser.fetch_product_detail_payload(product_url, category_name)
                    if not payload:
                        failed += 1
                        continue

                    product = product_dict_to_product(payload)
                    comments = comment_service.fetch_comments(
                        product_id=product.product_id,
                        product_url=product_url,
                        product_payload=payload,
                    )

                    repo.save_product(product)
                    if comments:
                        repo.save_comments(comments)
                        total_comments += len(comments)

                    total_crawled += 1
                    comment_info = f"({len(comments)} comments)" if comments else "(no comments)"
                    logger.info(
                        f"  [{total_crawled}/{MAX_PRODUCTS_TOTAL}] "
                        f"{product.name[:55]}... {comment_info}"
                    )
                except Exception as e:
                    failed += 1
                    logger.warning(
                        f"  [NETWORK] Product pipeline error (skip): {product_url[:60]}... — {e}"
                    )
                    logger.debug(traceback.format_exc())

    except KeyboardInterrupt:
        logger.info("\nCrawl interrupted by user")
    finally:
        repo.export_json(JSON_PATH)
        logger.info("\n" + "=" * 60)
        logger.info("CRAWL COMPLETE")
        logger.info(f"  Products:  {total_crawled}")
        logger.info(f"  Comments:  {total_comments}")
        logger.info(f"  Failed:    {failed}")
        logger.info(f"  DB:        {DB_PATH}")
        logger.info("=" * 60)
        repo.close()
        static_fetcher.close()
        dynamic_fetcher.close()


def serve() -> None:
    import uvicorn

    logger.info("Starting API server...")
    logger.info("Docs: http://127.0.0.1:8000/docs")
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py crawl   — Crawl sản phẩm (hybrid)")
        print("  python main.py serve   — Start API server")
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == "crawl":
        crawl()
    elif command == "serve":
        serve()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
