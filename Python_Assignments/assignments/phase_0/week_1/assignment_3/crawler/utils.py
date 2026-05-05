from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests import RequestException


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}


def same_domain(url_a: str, url_b: str) -> bool:
    return urlparse(url_a).netloc == urlparse(url_b).netloc


def fetch_links(
    url: str,
    include_external: bool = False,
    timeout: float = 10.0,
    headers: dict[str, str] | None = None,
) -> list[str]:
    try:
        response = requests.get(url, headers=headers or DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
    except RequestException:
        # Lỗi cũ: bắt Exception quá rộng và nuốt hết lỗi.
        # Sửa: chỉ bắt lỗi mạng/HTTP để không che giấu bug lập trình ngoài ý muốn.
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        next_url = urljoin(url, tag["href"])
        parsed = urlparse(next_url)

        if parsed.scheme not in {"http", "https"}:
            continue

        if not include_external and not same_domain(url, next_url):
            continue

        links.append(next_url)

    return links
