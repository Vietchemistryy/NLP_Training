from collections.abc import Callable
from functools import wraps
from time import sleep


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (TimeoutError, ConnectionError),
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay

            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as error:
                    attempt += 1
                    if attempt >= max_retries:
                        # Lỗi cũ: retry logic chỉ nằm trong một hàm cụ thể.
                        # Sửa: đưa ra decorator để tái sử dụng cho nhiều API call.
                        raise error

                    sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator
