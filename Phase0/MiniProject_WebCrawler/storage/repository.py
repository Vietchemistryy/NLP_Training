"""
SQLite repository với FTS5 full-text search.
Tách biệt data access — crawler/search không biết SQL.
"""

import json
import sqlite3

from storage.models import Comment, Product
from utils import setup_logging

logger = setup_logging("repository")


class ProductRepository:
    """SQLite + FTS5 CRUD cho products và comments."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Tạo bảng products, comments, và FTS5 virtual table."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id   INTEGER PRIMARY KEY,
                url          TEXT UNIQUE NOT NULL,
                name         TEXT NOT NULL,
                description_short TEXT DEFAULT '',
                description_long  TEXT DEFAULT '',
                category     TEXT DEFAULT '',
                crawled_at   TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                comment_id   INTEGER PRIMARY KEY,
                product_id   INTEGER NOT NULL,
                user         TEXT DEFAULT '',
                content      TEXT NOT NULL,
                evaluation   INTEGER DEFAULT 0,
                created_at   TEXT DEFAULT '',
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)

        # FTS5 virtual table cho full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
                name,
                description_short,
                description_long,
                content='products',
                content_rowid='product_id'
            )
        """)

        # Triggers để sync FTS5 với products table
        cursor.executescript("""
            CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products BEGIN
                INSERT INTO products_fts(rowid, name, description_short, description_long)
                VALUES (new.product_id, new.name, new.description_short, new.description_long);
            END;

            CREATE TRIGGER IF NOT EXISTS products_ad AFTER DELETE ON products BEGIN
                INSERT INTO products_fts(products_fts, rowid, name, description_short, description_long)
                VALUES ('delete', old.product_id, old.name, old.description_short, old.description_long);
            END;

            CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products BEGIN
                INSERT INTO products_fts(products_fts, rowid, name, description_short, description_long)
                VALUES ('delete', old.product_id, old.name, old.description_short, old.description_long);
                INSERT INTO products_fts(rowid, name, description_short, description_long)
                VALUES (new.product_id, new.name, new.description_short, new.description_long);
            END;
        """)

        self.conn.commit()

    def save_product(self, product: Product) -> bool:
        """Lưu sản phẩm. Return True nếu thành công, False nếu trùng."""
        try:
            self.conn.execute(
                """INSERT OR IGNORE INTO products
                   (product_id, url, name, description_short, description_long, category, crawled_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    product.product_id,
                    product.url,
                    product.name,
                    product.description_short,
                    product.description_long,
                    product.category,
                    product.crawled_at,
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Save product failed: {e}")
            return False

    def save_comments(self, comments: list[Comment]) -> int:
        """Lưu danh sách comments. Return số comment đã lưu."""
        saved = 0
        for c in comments:
            try:
                self.conn.execute(
                    """INSERT OR IGNORE INTO comments
                       (comment_id, product_id, user, content, evaluation, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (c.comment_id, c.product_id, c.user, c.content, c.evaluation, c.created_at),
                )
                saved += 1
            except sqlite3.Error:
                continue
        self.conn.commit()
        return saved

    def get_product(self, product_id: int) -> dict | None:
        """Lấy chi tiết 1 sản phẩm kèm comments."""
        row = self.conn.execute(
            "SELECT * FROM products WHERE product_id = ?", (product_id,)
        ).fetchone()
        if not row:
            return None

        product = dict(row)
        comments = self.conn.execute(
            "SELECT * FROM comments WHERE product_id = ? ORDER BY created_at DESC",
            (product_id,),
        ).fetchall()
        product["comments"] = [dict(c) for c in comments]
        return product

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Full-text search với BM25 ranking."""
        if not query or not query.strip():
            return []

        try:
            rows = self.conn.execute(
                """SELECT p.*, bm25(products_fts) AS score
                   FROM products_fts fts
                   JOIN products p ON fts.rowid = p.product_id
                   WHERE products_fts MATCH ?
                   ORDER BY score
                   LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            # FTS5 query syntax error — fallback LIKE search
            logger.warning(f"FTS5 query failed for '{query}', falling back to LIKE")
            rows = self.conn.execute(
                """SELECT *, 0.0 AS score FROM products
                   WHERE name LIKE ? OR description_short LIKE ? OR description_long LIKE ?
                   LIMIT ?""",
                (f"%{query}%", f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        """Thống kê tổng quan."""
        products = self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        comments = self.conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
        categories = self.conn.execute(
            "SELECT COUNT(DISTINCT category) FROM products"
        ).fetchone()[0]
        return {
            "total_products": products,
            "total_comments": comments,
            "total_categories": categories,
        }

    def url_exists(self, url: str) -> bool:
        """Check xem URL đã crawl chưa (chống trùng)."""
        row = self.conn.execute(
            "SELECT 1 FROM products WHERE url = ?", (url,)
        ).fetchone()
        return row is not None

    def export_json(self, filepath: str) -> None:
        """Export toàn bộ data ra JSON file (debug/inspect)."""
        rows = self.conn.execute("SELECT * FROM products ORDER BY product_id").fetchall()
        products = []
        for row in rows:
            product = dict(row)
            comments = self.conn.execute(
                "SELECT * FROM comments WHERE product_id = ?",
                (product["product_id"],),
            ).fetchall()
            product["comments"] = [dict(c) for c in comments]
            products.append(product)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(products)} products to {filepath}")

    def close(self):
        """Đóng kết nối DB."""
        self.conn.close()
