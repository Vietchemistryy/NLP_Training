"""
Web Crawler sử dụng OOP:
  1. Abstraction:  DeepCrawlStrategy (ABC) định nghĩa contract
  2. Encapsulation: CrawlerRunConfig gói cấu hình, _dfs/_bfs là private
  3. Inheritance:   BFS/DFSDeepCrawlStrategy kế thừa từ DeepCrawlStrategy
  4. Polymorphism:  WebCrawler.run() gọi strategy.crawl() - không biết BFS hay DFS
"""

import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urljoin, urlparse


# Encapsulation: gói toàn bộ cấu hình vào một object
class CrawlerRunConfig:
    def __init__(
        self,
        deep_crawl_strategy,          # Strategy instance (BFS hoặc DFS)
        max_depth: int = 2,           # Đâm sâu tối đa
        max_pages: int = 50,          # Lấy tối đa bao nhiêu trang
        same_domain_only: bool = True, # Chỉ crawl trong cùng domain
        timeout: float = 10.0,
        headers: dict | None = None,
    ):
        self.deep_crawl_strategy = deep_crawl_strategy
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.same_domain_only = same_domain_only
        self.timeout = timeout
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/123.0.0.0 Safari/537.36",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        }


# Abstraction: ABC định nghĩa contract - subclass phải implement crawl()
class DeepCrawlStrategy(ABC):
    @abstractmethod
    def crawl(self, start_url: str, max_depth: int, max_pages: int,
              fetcher) -> list[dict]:
        """Crawl từ start_url, trả về list các page đã thu thập."""
        pass


# Inheritance + Encapsulation: BFS strategy, _bfs là private helper
class BFSDeepCrawlStrategy(DeepCrawlStrategy):
    """Duyệt theo chiều rộng (BFS) - dùng deque làm queue."""

    def crawl(self, start_url, max_depth, max_pages, fetcher) -> list[dict]:
        results = []
        visited: set[str] = set()
        queue = deque([(start_url, 0)])

        while queue and len(results) < max_pages:
            url, depth = queue.popleft()
            if url in visited:
                continue
            visited.add(url)
            results.append({"url": url, "depth": depth})

            if depth >= max_depth:
                continue

            links = fetcher.fetch_links(url)
            for link in links:
                if link not in visited:
                    queue.append((link, depth + 1))

        return results


# Inheritance + Encapsulation: DFS strategy, _dfs là private recursive helper
class DFSDeepCrawlStrategy(DeepCrawlStrategy):
    """Duyệt theo chiều sâu (DFS)- dùng đệ quy."""

    def crawl(self, start_url, max_depth, max_pages, fetcher) -> list[dict]:
        results = []
        visited: set[str] = set()
        self._dfs(start_url, 0, max_depth, max_pages, fetcher, visited, results)
        return results

    def _dfs(self, url, depth, max_depth, max_pages, fetcher, visited, results):
        """Private recursive helper — encapsulation: không gọi từ ngoài."""
        if url in visited or len(results) >= max_pages:
            return
        visited.add(url)
        results.append({"url": url, "depth": depth})

        if depth >= max_depth:
            return

        links = fetcher.fetch_links(url)
        for link in links:
            if len(results) >= max_pages:
                return
            self._dfs(link, depth + 1, max_depth, max_pages,
                       fetcher, visited, results)


# Encapsulation: Fetcher gói logic HTTP + domain filtering
class Fetcher:
    """Fetch HTML và extract links - gói HTTP logic, ẩn chi tiết"""

    def __init__(self, base_domain: str, same_domain_only: bool,
                 timeout: float, headers: dict):
        self._base_domain = base_domain
        self._same_domain_only = same_domain_only
        self._timeout = timeout
        self._headers = headers

    def fetch_links(self, url: str) -> list[str]:
        """GET url, parse <a href>, trả về danh sách link hợp lệ."""
        try:
            response = requests.get(url, headers=self._headers,
                                    timeout=self._timeout)
            if response.status_code != 200:
                return []
        except Exception:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for tag in soup.find_all("a", href=True):
            next_url = urljoin(url, tag["href"])
            parsed = urlparse(next_url)
            if parsed.scheme not in ("http", "https"):
                continue
            if self._same_domain_only and parsed.netloc != self._base_domain:
                continue
            links.append(next_url)
        return links


class WebCrawler:
    """Điều phối crawl - sử dụng strategy pattern (polymorphism)."""

    def run(self, url: str, config: CrawlerRunConfig) -> list[dict]:
        """Entry point duy nhất - abstraction: ẩn toàn bộ workflow."""
        base_domain = urlparse(url).netloc

        fetcher = Fetcher(
            base_domain=base_domain,
            same_domain_only=config.same_domain_only,
            timeout=config.timeout,
            headers=config.headers,
        )

        # Polymorphism: gọi crawl() qua interface chung
        # Python dispatch tới BFS hay DFS tùy object thực tế trong config
        return config.deep_crawl_strategy.crawl(
            start_url=url,
            max_depth=config.max_depth,
            max_pages=config.max_pages,
            fetcher=fetcher,
        )


if __name__ == "__main__":
    crawler = WebCrawler()

    config = CrawlerRunConfig(
        deep_crawl_strategy=DFSDeepCrawlStrategy(),
        max_depth=10,
        max_pages=10,
        same_domain_only=True,
    )

    pages = crawler.run("https://chiaki.vn", config)
    for i, page in enumerate(pages, 1):
        print(f"{i}. [depth={page['depth']}] {page['url']}")
