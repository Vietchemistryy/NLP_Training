"""
FastAPI server: expose search + product detail API.
"""

import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import DB_PATH
from search.search_service import SearchService
from storage.repository import ProductRepository

# --- Khởi tạo dependencies ---
repo = ProductRepository(DB_PATH)
search_service = SearchService(repo)

# --- FastAPI app ---
app = FastAPI(
    title="Chiaki Product Search API",
    description="Crawl & search sản phẩm từ chiaki.vn — Phase 0 Demo",
    version="2.0.0",
)

# --- Mount static files ---
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def root():
    """Serve search UI."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health")
def health():
    """Health check + thống kê nhanh."""
    stats = repo.get_stats()
    return {"status": "ok", **stats}


@app.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm"),
    limit: int = Query(20, ge=1, le=100, description="Số kết quả tối đa"),
):
    """Full-text search sản phẩm (BM25 ranking)."""
    results = search_service.search(q, limit)
    return {
        "query": q,
        "total": len(results),
        "results": results,
    }


@app.get("/product/{product_id}")
def get_product(product_id: int):
    """Lấy chi tiết sản phẩm kèm comments."""
    product = repo.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/stats")
def stats():
    """Thống kê tổng quan."""
    return repo.get_stats()
