"""
Headless browser client (Playwright).
Chiaki.vn là SPA — cần browser thật để render JS.
"""

import random
import time

from playwright.sync_api import sync_playwright, Browser, Page

from config import DELAY_RANGE, MAX_RETRIES, USER_AGENTS
from utils import setup_logging

logger = setup_logging("fetcher")


class Fetcher:
    """Headless Chromium browser client."""

    def __init__(self, delay_range: tuple[float, float] = DELAY_RANGE):
        self.delay_range = delay_range
        self._playwright = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    def init_session(self) -> bool:
        """Khởi tạo Playwright browser."""
        try:
            logger.info("Starting headless browser...")
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._page = self._browser.new_page(
                user_agent=random.choice(USER_AGENTS)
            )
            logger.info("Navigating to chiaki.vn...")
            self._page.goto("https://chiaki.vn/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            logger.info("Browser session initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to init browser: {e}")
            return False

    def _delay(self):
        """Random sleep."""
        time.sleep(random.uniform(*self.delay_range))

    def evaluate_on_page(self, url: str | None, js_code: str):
        """Navigate tới URL (nếu có), chạy JS code trên DOM.

        Args:
            url: URL cần navigate. None = chạy trên page hiện tại.
            js_code: JavaScript function string.

        Returns:
            Kết quả từ JS execution.
        """
        if not self._page:
            logger.error("Browser not initialized")
            return None

        for attempt in range(1, MAX_RETRIES + 1):
            self._delay()
            try:
                if url is not None:
                    self._page.goto(url, wait_until="networkidle", timeout=30000)
                    time.sleep(1)
                result = self._page.evaluate(js_code)
                return result
            except Exception as e:
                logger.warning(
                    f"evaluate_on_page attempt {attempt}/{MAX_RETRIES} failed: "
                    f"{url} — {e}"
                )
                if attempt == MAX_RETRIES:
                    logger.error(f"evaluate_on_page gave up after {MAX_RETRIES} retries: {url}")
                    return None
                # Exponential backoff: 2s, 4s, ...
                time.sleep(2 * attempt)

    def fetch_api_from_page(self, api_url: str) -> dict | None:
        """Gọi API từ browser context (XHR, bypass CORS/auth).

        Chiaki API trả 'Access Denied' nếu gọi trực tiếp (thiếu cookie).
        Gọi từ browser context = tự mang cookie → bypass.
        """
        if not self._page:
            return None

        for attempt in range(1, MAX_RETRIES + 1):
            self._delay()
            try:
                result = self._page.evaluate(f"""
                    () => {{
                        return new Promise((resolve) => {{
                            const xhr = new XMLHttpRequest();
                            xhr.open('GET', '{api_url}', true);
                            xhr.withCredentials = true;
                            xhr.setRequestHeader('Accept', 'application/json');
                            xhr.onload = () => {{
                                try {{
                                    resolve(JSON.parse(xhr.responseText));
                                }} catch(e) {{
                                    resolve(null);
                                }}
                            }};
                            xhr.onerror = () => resolve(null);
                            xhr.timeout = 10000;
                            xhr.ontimeout = () => resolve(null);
                            xhr.send();
                        }});
                    }}
                """)
                # Check for API-level denial
                if isinstance(result, dict) and result.get("status") == "fail":
                    logger.warning(
                        f"API denied attempt {attempt}/{MAX_RETRIES}: "
                        f"{result.get('message', 'unknown')}"
                    )
                    if attempt == MAX_RETRIES:
                        return None
                    time.sleep(2 * attempt)
                    continue
                return result
            except Exception as e:
                logger.warning(
                    f"fetch_api_from_page attempt {attempt}/{MAX_RETRIES} failed: {e}"
                )
                if attempt == MAX_RETRIES:
                    logger.error(f"fetch_api_from_page gave up after {MAX_RETRIES} retries")
                    return None
                time.sleep(2 * attempt)

    def close(self):
        """Cleanup browser."""
        try:
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            logger.info("Browser closed")
        except Exception:
            pass
