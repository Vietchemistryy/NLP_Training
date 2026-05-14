"""
Dynamic fetcher: Playwright sync_api — chỉ launch khi cần.
- Chặn image, font, stylesheet; tùy chọn chặn script tracking.
- Intercept XHR/Fetch (ưu tiên) cho API comment.
- Retry navigate + exponential backoff.
- get_cookies() → sync sang requests.Session.
"""

from __future__ import annotations

import json
import random
import time
from typing import Any, Callable

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Response,
    Route,
    sync_playwright,
)

from config import (
    CHIAKI_ORIGIN,
    COMMENT_API_URL_HINTS,
    DELAY_RANGE,
    MAX_RETRIES,
    TRACKING_SCRIPT_HINTS,
    USER_AGENTS,
)
from utils import setup_logging

logger = setup_logging("dynamic_fetcher")


def _matches_api_hint(url: str) -> bool:
    u = url.lower()
    return any(h.lower() in u for h in COMMENT_API_URL_HINTS)


class DynamicFetcher:
    """Headless Chromium — spawn/teardown gọn; đóng hẳn sau close()."""

    def __init__(
        self,
        delay_range: tuple[float, float] = DELAY_RANGE,
        block_tracking_scripts: bool = True,
    ) -> None:
        self.delay_range = delay_range
        self.block_tracking_scripts = block_tracking_scripts
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self.is_active = False
        self._current_user_agent: str = random.choice(USER_AGENTS)

    def init_session(self) -> bool:
        if self.is_active:
            return True
        try:
            logger.info("[DYNAMIC] Starting headless browser...")
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._context = self._browser.new_context(
                user_agent=self._current_user_agent,
                locale="vi-VN",
                extra_http_headers={
                    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.7,en;q=0.6",
                },
            )
            self._page = self._context.new_page()
            self._page.route("**/*", self._route_interceptor)
            self.is_active = True
            return True
        except Exception as e:
            logger.error(f"[DYNAMIC] Failed to init browser: {e}")
            self.close()
            return False

    def _route_interceptor(self, route: Route) -> None:
        rtype = route.request.resource_type
        if rtype in ("image", "media", "font", "stylesheet"):
            route.abort()
            return
        if self.block_tracking_scripts and rtype == "script":
            url = route.request.url.lower()
            if any(t in url for t in TRACKING_SCRIPT_HINTS):
                route.abort()
                return
        route.continue_()

    def _delay(self) -> None:
        time.sleep(random.uniform(*self.delay_range))

    def align_user_agent_with_static(self, user_agent: str) -> None:
        """Đồng bộ UA với requests trước khi init (gọi trước init_session)."""
        self._current_user_agent = user_agent

    def navigate(self, url: str, wait_selector: str | None = None) -> bool:
        if not self.init_session() or not self._page:
            return False

        logger.info(f"[DYNAMIC] Navigating to: {url}")
        for attempt in range(1, MAX_RETRIES + 1):
            self._delay()
            try:
                self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
                if wait_selector:
                    try:
                        self._page.wait_for_selector(wait_selector, timeout=15000)
                    except Exception:
                        logger.warning(
                            f"[DYNAMIC] wait_for_selector timeout: {wait_selector!r} — continuing"
                        )
                self._page.wait_for_timeout(800)
                return True
            except Exception as e:
                logger.warning(f"[DYNAMIC] navigate attempt {attempt}/{MAX_RETRIES}: {e}")
                if attempt == MAX_RETRIES:
                    logger.error(f"[DYNAMIC] Failed to navigate: {url}")
                    return False
                time.sleep(2**attempt)
        return False

    def get_cookies(self) -> dict[str, str]:
        if not self._context:
            return {}
        return {c["name"]: c["value"] for c in self._context.cookies()}

    def sync_cookies_to_requests(self, update_cookies: Callable[[dict[str, str]], None]) -> None:
        cookies = self.get_cookies()
        if cookies:
            update_cookies(cookies)
            logger.info("[DYNAMIC] Cookies synced to requests session")

    def collect_comment_api_via_intercept(
        self,
        product_url: str,
        extra_wait_ms: int = 2500,
    ) -> dict[str, Any] | None:
        """[API_INTERCEPT] Lắng nghe response chứa load_comment."""
        if not self.init_session() or not self._page:
            return None

        captured: list[dict[str, Any]] = []

        def on_response(response: Response) -> None:
            try:
                if response.request.resource_type not in ("xhr", "fetch"):
                    return
                if not _matches_api_hint(response.url):
                    return
                body = response.text()
                if not body:
                    return
                data = json.loads(body)
                if isinstance(data, dict):
                    captured.append(data)
                    logger.info(f"[API_INTERCEPT] Captured: {response.url[:80]}...")
            except Exception:
                pass

        self._page.on("response", on_response)
        try:
            if not self.navigate(product_url):
                return None
            self._page.wait_for_timeout(extra_wait_ms)
        finally:
            try:
                self._page.remove_listener("response", on_response)
            except Exception:
                pass

        for item in captured:
            if item.get("status") != "fail" and ("data" in item or "result" in item):
                return item
        if captured:
            return captured[0]
        logger.warning("[API_INTERCEPT] No matching XHR/Fetch payload for comments")
        return None

    def fetch_api_from_page(self, api_url: str, context_url: str | None = None) -> dict | None:
        if not self.init_session() or not self._page:
            return None

        target = context_url or CHIAKI_ORIGIN
        safe_api = api_url.replace("\\", "\\\\").replace("'", "\\'")

        if not self.navigate(target):
            logger.error("[DYNAMIC] Cannot ensure browser context — skipping API call")
            return None

        for attempt in range(1, MAX_RETRIES + 1):
            self._delay()
            try:
                logger.info(f"[DYNAMIC] XHR evaluate API: {api_url[:100]}...")
                result = self._page.evaluate(
                    f"""
                    () => new Promise((resolve) => {{
                        const xhr = new XMLHttpRequest();
                        xhr.open('GET', '{safe_api}', true);
                        xhr.withCredentials = true;
                        xhr.setRequestHeader('Accept', 'application/json');
                        xhr.onload = () => {{
                            try {{ resolve(JSON.parse(xhr.responseText)); }}
                            catch (e) {{ resolve(null); }}
                        }};
                        xhr.onerror = () => resolve(null);
                        xhr.timeout = 15000;
                        xhr.ontimeout = () => resolve(null);
                        xhr.send();
                    }})
                    """
                )

                if isinstance(result, dict) and result.get("status") == "fail":
                    logger.warning(
                        f"[DYNAMIC] API denied attempt {attempt}/{MAX_RETRIES}: "
                        f"{result.get('message', 'unknown')}"
                    )
                    if attempt == MAX_RETRIES:
                        return None
                    self.navigate(target)
                    time.sleep(2 * attempt)
                    continue
                return result
            except Exception as e:
                logger.warning(f"[DYNAMIC] API call attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt == MAX_RETRIES:
                    return None
                time.sleep(2 * attempt)
        return None

    def evaluate(self, url: str | None, js_code: str) -> Any:
        if not self.init_session() or not self._page:
            return None
        if url and not self.navigate(url):
            return None
        for attempt in range(1, MAX_RETRIES + 1):
            self._delay()
            try:
                return self._page.evaluate(js_code)
            except Exception as e:
                logger.warning(f"[DYNAMIC] Evaluate attempt {attempt}/{MAX_RETRIES}: {e}")
                if attempt == MAX_RETRIES:
                    return None
                time.sleep(2 * attempt)
        return None

    @property
    def page(self) -> Page | None:
        return self._page

    def close(self) -> None:
        if not self.is_active:
            return
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            logger.info("[DYNAMIC] Browser closed")
        except Exception as e:
            logger.error(f"[DYNAMIC] Error closing browser: {e}")
        finally:
            self.is_active = False
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
