from dataclasses import dataclass, field

from .crawler.strategies.base import CrawlStrategy


@dataclass(slots=True)
class CrawlerConfig:
    strategy: CrawlStrategy
    max_depth: int = 2
    max_pages: int = 50
    include_external: bool = False
    timeout: float = 10.0
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if self.max_pages <= 0:
            raise ValueError("max_pages must be > 0")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")
