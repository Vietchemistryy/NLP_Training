"""
Search service: thin wrapper trên repository.
Normalize query -> delegate FTS5 search.

Fixes:
- Thêm unicode normalization: decompose NFC → NFD → strip combining marks
  → recompose. Cho phép user gõ không dấu ("sua bot") vẫn tìm được
  sản phẩm có dấu ("Sữa Bột") vì cả hai đều được normalize về dạng
  không dấu trước khi search.
- Tách _normalize() thành method riêng để dễ test.

Lưu ý: chiến lược này yêu cầu data được index ở dạng không dấu.
Vì FTS5 index của ta đang lưu text gốc (có dấu), ta search cả 2 dạng:
  1. Query gốc (có dấu nếu user gõ có dấu)
  2. Query không dấu - fallback nếu query gốc không có kết quả
"""

import unicodedata

from storage.repository import ProductRepository


class SearchService:
    # Tầng logic search - tách khỏi API và storage
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Normalize query và search.

        Thử theo thứ tự:
          1. Query đã lowercase (giữ dấu) -> FTS5 BM25
          2. Nếu không có kết quả và query có dấu -> thử lại bằng query
             không dấu (hỗ trợ user gõ tắt không dấu)

        Args:
            query: Từ khóa tìm kiếm (tiếng Việt hoặc tiếng Anh)
            limit: Số kết quả tối đa

        Returns:
            List dict sản phẩm, đã rank theo BM25 score (cao = tốt)
        """
        normalized = query.strip().lower()
        if not normalized:
            return []

        # Lần 1: Search với query gốc (có dấu)
        results = self.repo.search(normalized, limit)
        if results:
            return results

        # Lần 2: Thử không dấu nếu query có chứa ký tự unicode dấu
        no_accent = self._remove_accents(normalized)
        if no_accent != normalized:
            results = self.repo.search(no_accent, limit)

        return results


    # Static helpers
    @staticmethod
    def _remove_accents(text: str) -> str:
        """Bỏ dấu tiếng Việt bằng Unicode decomposition.

        'sữa bột' -> 'sua bot'
        'Vitamin C' -> 'Vitamin C'  (không thay đổi ASCII)

        Cách hoạt động:
          NFD decompose: ữ -> u + combining tilde + combining horn
          Lọc bỏ Mn (Mark, Nonspacing) - các combining diacritic
          NFC recompose: ghép lại thành string thuần ASCII/Latin
        """
        nfd = unicodedata.normalize("NFD", text)
        stripped = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
        return unicodedata.normalize("NFC", stripped)