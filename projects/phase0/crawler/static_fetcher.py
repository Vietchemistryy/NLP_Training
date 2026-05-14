"""
Static fetcher: requests.Session + retry (exponential backoff), timeout, rate limit.
Logging: [STATIC], [NETWORK].
Optional debug cache: .cache/ khi CACHE_DEBUG=1.
"""

from __future__ import annotations

import hashlib
import os
import random
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import CACHE_DEBUG, CACHE_DIR, DELAY_RANGE, MAX_RETRIES, REQUEST_TIMEOUT, USER_AGENTS
from utils import setup_logging

logger = setup_logging("static_fetcher")


def _cache_key(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return os.path.join(CACHE_DIR, f"static_{h}.txt")


def _maybe_read_cache(url: str) -> str | None:
    if not CACHE_DEBUG:
        return None
    path = _cache_key(url)
    if os.path.isfile(path):
        logger.info(f"[STATIC] Cache hit: {path}")
        with open(path, encoding="utf-8") as f:
            return f.read()
    return None


def _maybe_write_cache(url: str, text: str) -> None:
    if not CACHE_DEBUG:
        return
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_key(url)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    logger.debug(f"[STATIC] Cached HTML: {path}")


class StaticFetcher:
    """HTTP client cho HTML/API tĩnh — dùng chung một Session."""

    def __init__(
        self,
        delay_range: tuple[float, float] = DELAY_RANGE,
        timeout: tuple[float, float] | float = REQUEST_TIMEOUT,
    ) -> None:
        self.delay_range = delay_range
        self.timeout = timeout
        self.session = requests.Session()

        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session.headers.update(
            {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.7,en;q=0.6",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def _delay(self) -> None:
        time.sleep(random.uniform(*self.delay_range))

    def update_cookies(self, cookies: dict[str, str]) -> None:
        """Đồng bộ cookie từ Playwright (hoặc nguồn khác) vào Session."""
        self.session.cookies.update(cookies)
        logger.info("[STATIC] Cookies updated from external source")

    def set_referer(self, referer: str) -> None:
        self.session.headers["Referer"] = referer

    def align_user_agent(self, user_agent: str) -> None:
        """Đồng bộ UA với Playwright để giảm mismatch anti-bot."""
        self.session.headers["User-Agent"] = user_agent
        logger.debug("[STATIC] User-Agent aligned with browser")

    def rotate_user_agent(self) -> None:
        ua = random.choice(USER_AGENTS)
        self.session.headers["User-Agent"] = ua
        logger.debug(f"[STATIC] Rotated User-Agent: {ua[:50]}...")

    def get(self, url: str, **kwargs: Any) -> requests.Response | None:
        self._delay()
        headers = dict(self.session.headers)
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        if random.random() < 0.15:
            self.rotate_user_agent()
            headers["User-Agent"] = self.session.headers["User-Agent"]

        try:
            response = self.session.get(url, timeout=self.timeout, headers=headers, **kwargs)
            if response.status_code == 403:
                logger.warning(f"[STATIC] 403 Forbidden: {url}")
                return response
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout as e:
            logger.error(f"[NETWORK] Timeout for {url}: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[NETWORK] Connection error for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"[STATIC] Request failed for {url}: {e}")
            return None

    def get_html(self, url: str) -> str | None:
        cached = _maybe_read_cache(url)
        if cached is not None:
            return cached

        response = self.get(url)
        if response and response.status_code == 200:
            text = response.text
            _maybe_write_cache(url, text)
            return text
        return None

    def get_json(self, url: str, **kwargs: Any) -> dict | None:
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/json")
        response = self.get(url, headers=headers, **kwargs)
        if response and response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                logger.error(f"[STATIC] Invalid JSON response from {url}")
        return None

    def close(self) -> None:
        self.session.close()
