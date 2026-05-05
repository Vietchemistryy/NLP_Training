from Python_Assignments.assignments.phase_0.week_1.assignment_3.config import CrawlerConfig
from Python_Assignments.assignments.phase_0.week_1.assignment_3.crawler.crawler import WebCrawler
from Python_Assignments.assignments.phase_0.week_1.assignment_3.crawler.strategies import DFSStrategy


def main() -> None:
    crawler = WebCrawler()

    # Ví dụ DFS.
    config = CrawlerConfig(
        sdụategy=DFSStrategy(),
        max_depth=2,
        max_pages=10,
        include_external=False,
    )

    pages = crawler.run("https://example.com", config)
    for index, page in enumerate(pages, start=1):
        print(f"{index}. [depth={page['depth']}] {page['url']} ({page['strategy']})")


if __name__ == "__main__":
    main()
