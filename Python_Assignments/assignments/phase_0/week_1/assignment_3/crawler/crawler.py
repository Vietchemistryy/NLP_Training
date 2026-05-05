from .config import CrawlerConfig
from .utils import fetch_links


class WebCrawler:
    def run(self, url: str, config: CrawlerConfig) -> list[dict]:
        # Lỗi cũ: một class lớn giữ hết logic, khó test và khó thay strategy.
        # Sửa: chỉ giữ orchestration ở đây, còn traversal nằm ở strategy riêng.
        return config.strategy.crawl(
            start_url=url,
            fetch_links=lambda current_url: fetch_links(
                current_url,
                include_external=config.include_external,
                timeout=config.timeout,
                headers=config.headers or None,
            ),
            max_depth=config.max_depth,
            max_pages=config.max_pages,
        )
