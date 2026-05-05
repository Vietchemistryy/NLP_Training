from .base import CrawlStrategy, FetchLinksFn


class DFSStrategy(CrawlStrategy):
    def crawl(
        self,
        start_url: str,
        fetch_links: FetchLinksFn,
        max_depth: int,
        max_pages: int,
    ) -> list[dict]:
        results: list[dict] = []
        visited: set[str] = set()
        stack = [(start_url, 0)]

        while stack and len(results) < max_pages:
            url, depth = stack.pop()

            if url in visited:
                continue

            visited.add(url)
            results.append({"url": url, "depth": depth, "strategy": "DFS"})

            if depth >= max_depth:
                continue

            # Lỗi cũ: DFS dùng đệ quy nên dễ chạm recursion limit khi crawl sâu.
            # Sửa: chuyển sang stack tường minh để kiểm soát độ sâu an toàn hơn.
            next_urls = fetch_links(url)
            for next_url in reversed(next_urls):
                if next_url not in visited:
                    stack.append((next_url, depth + 1))

        return results
