"""
CLI entrypoint: crawl hoặc serve.

Usage:
    python main.py crawl     # Crawl sản phẩm từ chiaki.vn
    python main.py serve     # Start FastAPI server
"""

import os
import sys

from config import CATEGORIES, DATA_DIR, DB_PATH, JSON_PATH, MAX_PRODUCTS_TOTAL
from crawler.comment_service import CommentService
from crawler.fetcher import Fetcher
from crawler.parser import ProductParser
from storage.repository import ProductRepository
from utils import setup_logging

logger = setup_logging("main")


def crawl():
    """Crawl chiaki.vn:
    1. Browser navigate category page → click "Xem thêm" → extract all product URLs
    2. Navigate từng product page → extract details
    3. XHR call comment API → extract comments
    4. Save SQLite + JSON
    """
    logger.info("=" * 60)
    logger.info("Starting crawl...")
    logger.info(f"Target: {len(CATEGORIES)} categories, max {MAX_PRODUCTS_TOTAL} products")
    logger.info("=" * 60)

    os.makedirs(DATA_DIR, exist_ok=True)

    fetcher = Fetcher()
    if not fetcher.init_session():
        logger.error("Cannot init browser, aborting")
        return

    parser = ProductParser(fetcher)
    comment_service = CommentService(fetcher)
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

            # Fetch all product links from category (with "Xem thêm" clicks)
            product_links = parser.fetch_product_list(category_url)
            if not product_links:
                logger.info(f"  No products found")
                continue

            logger.info(f"  Found {len(product_links)} products in category")

            for link_data in product_links:
                if total_crawled >= MAX_PRODUCTS_TOTAL:
                    break

                product_url = link_data["url"]

                if repo.url_exists(product_url):
                    continue

                # Navigate to product page → extract details
                product = parser.fetch_product_detail(product_url, category_name)
                if not product:
                    failed += 1
                    continue

                # Fetch comments
                comments = comment_service.fetch_comments(product.product_id)

                # Save
                repo.save_product(product)
                if comments:
                    repo.save_comments(comments)
                    total_comments += len(comments)

                total_crawled += 1
                comment_info = f"({len(comments)} comments)" if comments else ""
                logger.info(
                    f"  [{total_crawled}/{MAX_PRODUCTS_TOTAL}] "
                    f"{product.name[:55]}... {comment_info}"
                )

    except KeyboardInterrupt:
        logger.info("\nCrawl interrupted by user")
    finally:
        repo.export_json(JSON_PATH)
        logger.info("\n" + "=" * 60)
        logger.info("CRAWL COMPLETE")
        logger.info(f"  Products: {total_crawled}")
        logger.info(f"  Comments: {total_comments}")
        logger.info(f"  Failed:   {failed}")
        logger.info(f"  DB:       {DB_PATH}")
        logger.info("=" * 60)
        repo.close()
        fetcher.close()


def serve():
    """Start FastAPI server."""
    import uvicorn

    logger.info("Starting API server...")
    logger.info("Docs: http://127.0.0.1:8000/docs")
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py crawl   — Crawl sản phẩm")
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
