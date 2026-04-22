import requests
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urljoin, urlparse

# Tránh web tưởng bot
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}


def crawl(
        url: str,
        strategy: str = "BFS",
        max_depth: int = 2, # Đâm sâu tối đa: 2 tầng, giả sử A(depth0) -> B(depth1) -> C(depth2) -> D(Depth3) (Tịt)
        max_pages: int = 50, # Lấy tối đa 50 cái, chẳng hạn như lấy tối đa 50 links trên trang
        include_external: bool = False # Có mở rộng hay không? (Tức là đi ra ngoài domain)
):
    # Validate
    if strategy not in ("BFS", "DFS"):
        raise ValueError("strategy must be BFS or DFS")
    visited = set() # Lưu node đã thăm
    results = [] # Lưu kết quả
    base_domain = urlparse(url).netloc

    container = deque([(url, 0)]) if strategy == "BFS" else [(url, 0)] # BFS dùng queue, DFS dùng stack

    while container and len(visited) < max_pages:
        # Lấy phần tử
        if strategy == "BFS":
            current_url, depth = container.popleft() # Lấy thằng bên trái, ví dụ container = [B,C,D] -> Lấy B
        else:
            current_url, depth = container.pop() # Lấy thằng bên phải, ví dụ container = [B,C,D] -> Lấy D
        if current_url in visited:
            continue
        visited.add(current_url)
        results.append(current_url)
        # Kiểm soát depth
        if depth >= max_depth:
            continue # Không dùng break vì sẽ dừng hẳn while

        try:
            headers = HEADERS
            response = requests.get(current_url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                continue
        except Exception:
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup.find_all("a", href=True):
            href = tag.get("href")
            next_url = urljoin(current_url, href)
            parsed = urlparse(next_url)
            # chỉ lấy http/https
            if parsed.scheme not in ("http", "https"):
                continue
            # filter external
            if not include_external and parsed.netloc != base_domain:
                continue
            if next_url not in visited:
                container.append((next_url, depth + 1))
    return results


if __name__ == "__main__":
    urls = crawl(
        "https://chiaki.vn",
        strategy="DFS",
        max_depth=10,
        max_pages=10,
        include_external=False
    )
    for i, u in enumerate(urls, 1):
        print(f"{i}. {u}")
