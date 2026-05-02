"""
Cấu hình tập trung cho toàn bộ project.
Không hardcode trong code — sửa ở đây.
"""

import os

"""
Category configs: (display_name, category_id)
Chiaki.vn dùng Vue/Nuxt SPA — product listing load qua API, không HTML.
category_id lấy từ URL pattern trên site.
"""

CATEGORIES = [
    ("men-vi-sinh-cho-be", 194),
    ("ho-tro-giam-ho", 230),
    ("vitamin-cho-be", 256),
    ("sua-bot-cho-be", 25),
    ("bot-an-dam", 34),
    ("bang-ta-cho-be", 63),
    ("nuoc-giat-xa-vai", 602),
    ("dau-goi-sua-tam-cho-be", 120),
]

# Crawler limits
MAX_PRODUCTS_TOTAL = 500        # Tổng số sản phẩm tối đa
MAX_COMMENTS_PER_PRODUCT = 20   # Số comment tối đa mỗi sản phẩm
DELAY_RANGE = (1.0, 2.5)        # Random sleep giữa requests (giây)
MAX_RETRIES = 3                 # Số lần retry khi request fail

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "products.db")
JSON_PATH = os.path.join(DATA_DIR, "products.json")

# API endpoints (chiaki.vn dùng SPA → comment data qua API)
API_BASE = "https://api.chiaki.vn/api"
COMMENT_API_URL = f"{API_BASE}/load_comment"

# User-Agent rotation (tránh bị block)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

