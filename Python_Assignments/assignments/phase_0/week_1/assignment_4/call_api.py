import random

from .retry import retry


def call_api(url: str) -> dict:
    r = random.random()
    if r < 0.5:
        raise TimeoutError("Timeout")
    return {"status": 200, "data": "OK", "url": url}


@retry(max_retries=5, delay=1, backoff=2)
def call_api_with_retry(url: str) -> dict:
    # Lỗi cũ: retry nằm trong while-loop thủ công, khó tái sử dụng.
    # Sửa: chuyển sang decorator, giữ business logic của API call tách khỏi retry policy.
    return call_api(url)
