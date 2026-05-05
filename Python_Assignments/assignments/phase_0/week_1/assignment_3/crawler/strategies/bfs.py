from collections import deque

from .base import CrawlStrategy, FetchLinksFn


class BFSStrategy(CrawlStrategy):
    def crawl(
        self,
        start_url: str,
        fetch_links: FetchLinksFn,
        max_depth: int,
        max_pages: int,
    ) -> list[dict]:
        results: list[dict] = []
        visited: set[str] = set()
        queue = deque([(start_url, 0)])

        while queue and len(results) < max_pages:
            url, depth = queue.popleft()

            if url in visited:
                continue

            visited.add(url)
            results.append({"url": url, "depth": depth, "strategy": "BFS"})

            if depth >= max_depth:
                continue

            # Lỗi cũ: không tách rõ vai trò duyệt và vai trò lấy link.
            # Sửa: strategy chỉ điều phối thứ tự duyệt, còn việc parse HTML nằm ở utils.fetch_links.
            for next_url in fetch_links(url):
                if next_url not in visited:
                    queue.append((next_url, depth + 1))

        return results
