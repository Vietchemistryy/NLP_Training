from abc import ABC, abstractmethod
from collections.abc import Callable


FetchLinksFn = Callable[[str], list[str]]


class CrawlStrategy(ABC):
    @abstractmethod
    def crawl(
        self,
        start_url: str,
        fetch_links: FetchLinksFn,
        max_depth: int,
        max_pages: int,
    ) -> list[dict]:
        """Traverse links from a start URL and return crawled pages."""
