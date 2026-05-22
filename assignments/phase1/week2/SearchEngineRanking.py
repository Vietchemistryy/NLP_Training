"""
Assignment 10: Real-World Search Engine Ranking

Dataset: projects/phase0/data/products.json (Phase 0 crawl)
Pipeline: preprocess -> TF-IDF -> vectorize query -> cosine similarity -> rank

"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRODUCTS_PATH = _PROJECT_ROOT / "projects" / "phase0" / "data" / "products.json"


# Preprocess
def preprocess(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def build_document(product: dict) -> str:
    parts = [product.get("name", ""), product.get("description_short", "")]
    dl = (product.get("description_long") or "").strip()
    if dl and len(dl) > 30 and dl != "với .":
        parts.append(dl)
    return preprocess(" ".join(p.strip() for p in parts if p and str(p).strip()))


# TF-IDF
class TfidfIndex:
    def __init__(self):
        self.word2idx: dict[str, int] = {}
        self.idf: np.ndarray | None = None

    def fit(self, documents: list[str]) -> None:
        n_docs = len(documents)
        df: dict[str, int] = defaultdict(int)
        idx = 0

        for doc in documents:
            for word in set(tokenize(doc)):
                if word not in self.word2idx:
                    self.word2idx[word] = idx
                    idx += 1
                df[word] += 1

        vocab_size = len(self.word2idx)
        self.idf = np.zeros(vocab_size)
        for word, i in self.word2idx.items():
            self.idf[i] = math.log(n_docs / df[word])

    def _doc_vector(self, text: str) -> np.ndarray:
        assert self.idf is not None
        vec = np.zeros(len(self.idf))
        tokens = tokenize(text)
        if not tokens:
            return vec
        counts = Counter(tokens)
        total = len(tokens)
        for word, cnt in counts.items():
            if word in self.word2idx:
                i = self.word2idx[word]
                tf = cnt / total
                vec[i] = tf * self.idf[i]
        return vec

    def fit_transform(self, documents: list[str]) -> np.ndarray:
        self.fit(documents)
        return np.vstack([self._doc_vector(d) for d in documents])

    def transform_query(self, query: str) -> np.ndarray:
        return self._doc_vector(preprocess(query))


def cosine_similarity(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
    # cos(theta) = (A . B) / (|A| * |B|)
    q_norm = np.linalg.norm(query_vec)
    if q_norm == 0:
        return np.zeros(doc_matrix.shape[0])
    d_norms = np.linalg.norm(doc_matrix, axis=1)
    d_norms = np.where(d_norms == 0, 1.0, d_norms)
    return (doc_matrix @ query_vec) / (d_norms * q_norm)


# Search engine
def load_products(path: Path | None = None) -> list[dict]:
    p = path or PRODUCTS_PATH
    if not p.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {p}. Chạy crawl Phase 0: cd projects/phase0 && python main.py crawl"
        )
    with open(p, encoding="utf-8") as f:
        return json.load(f)


class SearchEngine:
    def __init__(self, products: list[dict] | None = None):
        self.products = products if products is not None else load_products()
        self.documents = [build_document(p) for p in self.products]
        self.index = TfidfIndex()
        self.doc_matrix = self.index.fit_transform(self.documents)

    def rank(self, query: str, top_k: int = 10) -> list[dict]:
        if not query.strip():
            return []
        q_vec = self.index.transform_query(query)
        scores = cosine_similarity(q_vec, self.doc_matrix)
        order = np.argsort(scores)[::-1]

        out = []
        for i in order[:top_k]:
            s = float(scores[i])
            if s <= 0:
                continue
            p = self.products[i]
            out.append(
                {
                    "rank": len(out) + 1,
                    "score": round(s, 4),
                    "product_id": p.get("product_id"),
                    "name": p.get("name"),
                    "category": p.get("category"),
                    "price": p.get("price"),
                    "url": p.get("url"),
                }
            )
        return out


def print_results(query: str, results: list[dict]) -> None:
    print(f'\nKết quả cho: "{query}"')
    if not results:
        print("  (không có kết quả)")
        return
    for r in results:
        name = (r.get("name") or "")[:85]
        print(f"  #{r['rank']}  score={r['score']:.4f}  |  {name}")


def interactive_search(top_k: int = 10) -> None:
    print("Đang index sản phẩm...")
    engine = SearchEngine()
    print(f"Xong. Đã index {len(engine.products)} sản phẩm.")
    print('Gõ từ khóa để tìm (Enter trống hoặc "quit" để thoát).\n')

    while True:
        try:
            query = input("Query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThoát.")
            break

        if not query or query.lower() in ("quit", "exit", "q"):
            print("Thoát.")
            break

        print_results(query, engine.rank(query, top_k=top_k))


if __name__ == "__main__":
    interactive_search()
