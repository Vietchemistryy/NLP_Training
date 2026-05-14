"""
SQLite repository với FTS5 full-text search.
Hybrid: cột price, images_json, rating_count, metadata_json + migrate DB cũ.
"""

import json
import sqlite3

from storage.models import Comment, Product
from utils import setup_logging

logger = setup_logging("repository")


class ProductRepository:
    """SQLite + FTS5 CRUD cho products và comments."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._migrate_products_columns()

    def _migrate_products_columns(self) -> None:
        """Thêm cột hybrid crawl (DB cũ không có)."""
        cur = self.conn.execute("PRAGMA table_info(products)")
        cols = {row[1] for row in cur.fetchall()}
        alters: list[str] = []
        if "price" not in cols:
            alters.append("ALTER TABLE products ADD COLUMN price TEXT DEFAULT ''")
        if "images_json" not in cols:
            alters.append("ALTER TABLE products ADD COLUMN images_json TEXT DEFAULT '[]'")
        if "rating_count" not in cols:
            alters.append("ALTER TABLE products ADD COLUMN rating_count INTEGER DEFAULT 0")
        if "metadata_json" not in cols:
            alters.append("ALTER TABLE products ADD COLUMN metadata_json TEXT DEFAULT '{}'")
        for sql in alters:
            try:
                self.conn.execute(sql)
            except sqlite3.OperationalError:
                pass
        self.conn.commit()

    def _create_tables(self) -> None:
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id   INTEGER PRIMARY KEY,
                url          TEXT UNIQUE NOT NULL,
                name         TEXT NOT NULL,
                description_short TEXT DEFAULT '',
                description_long  TEXT DEFAULT '',
                category     TEXT DEFAULT '',
                crawled_at   TEXT NOT NULL,
                price        TEXT DEFAULT '',
                images_json  TEXT DEFAULT '[]',
                rating_count INTEGER DEFAULT 0,
                metadata_json TEXT DEFAULT '{}'
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

        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
                name,
                description_short,
                description_long,
                content='products',
                content_rowid='product_id',
                tokenize='unicode61'
            )
        """)

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
        try:
            self.conn.execute(
                """INSERT OR IGNORE INTO products
                   (product_id, url, name, description_short, description_long, category, crawled_at,
                    price, images_json, rating_count, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    product.product_id,
                    product.url,
                    product.name,
                    product.description_short,
                    product.description_long,
                    product.category,
                    product.crawled_at,
                    product.price or "",
                    json.dumps(product.images or [], ensure_ascii=False),
                    int(product.rating_count or 0),
                    json.dumps(product.metadata or {}, ensure_ascii=False),
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Save product failed: {e}")
            return False

    def save_comments(self, comments: list[Comment]) -> int:
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
        if not query or not query.strip():
            return []
        escaped = self._escape_fts_query(query)
        try:
            rows = self.conn.execute(
                """SELECT p.*, bm25(products_fts) AS score
                   FROM products_fts fts
                   JOIN products p ON fts.rowid = p.product_id
                   WHERE products_fts MATCH ?
                   ORDER BY score
                   LIMIT ?""",
                (escaped, limit),
            ).fetchall()
            results = []
            for r in rows:
                row_dict = dict(r)
                raw_score = row_dict.get("score") or 0.0
                row_dict["score"] = round(abs(raw_score), 4)
                results.append(row_dict)
            return results
        except sqlite3.OperationalError as e:
            logger.warning(f"FTS5 query failed for '{escaped}': {e} — falling back to LIKE")
            rows = self.conn.execute(
                """SELECT *, 0.0 AS score FROM products
                   WHERE name LIKE ? OR description_short LIKE ? OR description_long LIKE ?
                   LIMIT ?""",
                (f"%{query}%", f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def _escape_fts_query(query: str) -> str:
        tokens = query.strip().split()
        if not tokens:
            return '""'
        escaped_tokens = [f'"{t.replace(chr(34), "")}"' for t in tokens]
        return " ".join(escaped_tokens)

    def get_stats(self) -> dict:
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
        row = self.conn.execute("SELECT 1 FROM products WHERE url = ?", (url,)).fetchone()
        return row is not None

    def export_json(self, filepath: str) -> None:
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

    def close(self) -> None:
        self.conn.close()
