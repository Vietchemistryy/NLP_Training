import time
import random


def call_api(url):
    r = random.random()
    if r < 0.5:
        raise TimeoutError("Timeout")
    else:
        return {"status": 200, "data": "OK"}


def call_api_with_retry(url, max_retries=3, base_delay=1, backoff=2):
    attempt = 0
    while attempt < max_retries:
        try:
            # Thực hiện gọi API
            return call_api(url)
        except (TimeoutError, ConnectionError) as e:
            attempt += 1
            # Nếu đã hết lượt retry thì raise lỗi ra ngoài
            if attempt >= max_retries:
                print(f"Failed after {max_retries} attempts.")
                raise e
            # Tính toán delay theo công thức: base_delay * (backoff ^ attempt)
            # Ở đây attempt bắt đầu từ 1 sau lần lỗi đầu tiên
            wait_time = base_delay * (backoff ** (attempt - 1))
            print(f"Error: {e}. Retrying in {wait_time}s (Attempt {attempt}/{max_retries})...")
            time.sleep(wait_time)


if __name__ == "__main__":
    try:
        response = call_api_with_retry(
            url="https://api.llm.model/v1",
            max_retries=5,
            base_delay=1,
            backoff=2
        )
        print(f"Success: {response}")
    except Exception as e:
        print(f"Final error: {e}")
