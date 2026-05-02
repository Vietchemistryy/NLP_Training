"""
Search service: thin wrapper trên repository.
Normalize query → delegate FTS5 search.
Thiết kế để sau có thể plug semantic search mà không đụng API/storage.
"""

from storage.repository import ProductRepository


class SearchService:
    """Tầng logic search — tách khỏi API và storage."""

    def __init__(self, repo: ProductRepository):
        self.repo = repo

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Normalize query và search.

        Args:
            query: Từ khóa tìm kiếm (tiếng Việt hoặc tiếng Anh).
            limit: Số kết quả tối đa.

        Returns:
            List dict sản phẩm, đã rank theo BM25 score.
        """
        normalized = query.strip().lower()
        if not normalized:
            return []
        return self.repo.search(normalized, limit)
