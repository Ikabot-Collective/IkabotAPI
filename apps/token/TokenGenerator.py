import logging
import os
import queue
import random
import threading
from concurrent.futures import Future

from playwright.sync_api import sync_playwright

import settings

logger = logging.getLogger(__name__)

DEFAULT_LOCALE = "en-GB"
DEFAULT_TIMEZONE_ID = "Europe/London"


class TokenGenerator:
    """
    TokenGenerator class for generating tokens using Playwright.

    A single dedicated worker thread owns the Playwright instance and a
    long-lived Chromium browser. Requests are queued (FIFO) and served one at a
    time, which prevents concurrent Playwright subprocess spawning (the
    "Racing with another loop" crashes with uvloop) and avoids paying the
    Chromium start-up cost for every token. Each token still gets its own fresh
    browser context, so no state is shared between tokens. The browser is
    relaunched every `BROWSER_RECYCLE_AFTER` tokens and after any failure.

    Usage:
    ```
    token_generator = TokenGenerator(supported_user_agents=["User Agent 1", "User Agent 2"])
    token = token_generator.get_token()
    ```
    """

    def __init__(self, supported_user_agents):
        """
        Initialize TokenGenerator.

        Args:
        - supported_user_agents: List of supported user agent strings.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.html_file_path = f"file:///{current_directory}/token.html"
        self.supported_user_agents = supported_user_agents
        self.default_locale = DEFAULT_LOCALE
        self.default_timezone_id = DEFAULT_TIMEZONE_ID
        self._jobs = queue.Queue()
        self._worker = None
        self._playwright = None
        self._browser = None
        self._served = 0
        self._worker_lock = threading.Lock()

    def _ensure_worker(self):
        with self._worker_lock:
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(
                    target=self._worker_loop, name="token-worker", daemon=True
                )
                self._worker.start()

    def get_token(
        self,
        user_agent: str = None,
        locale: str = None,
        timezone_id: str = None,
    ):
        """
        Generate a fresh blackbox token.

        Requests are queued and served one at a time by a worker thread that
        keeps a single browser open, which prevents uvloop race conditions
        when multiple requests arrive concurrently. When no
        user_agent is provided, a random one from the supported list is used.
        Empty locale and timezone values fall back to configured defaults.

        Args:
        - user_agent (str, optional): The user agent string to use for the browser.
        - locale (str, optional): Browser locale to use for token generation.
        - timezone_id (str, optional): Browser timezone to use for token generation.

        Returns:
        - str: The generated token.
        """
        effective_ua = user_agent if user_agent else random.choice(self.supported_user_agents)
        effective_locale = locale if locale else self.default_locale
        effective_timezone_id = (
            timezone_id if timezone_id else self.default_timezone_id
        )

        self._ensure_worker()
        future = Future()
        self._jobs.put(
            (future, effective_ua, effective_locale, effective_timezone_id)
        )
        return future.result()

    def _worker_loop(self):
        """Serve queued token requests, keeping one browser open between them."""
        try:
            while True:
                future, user_agent, locale, timezone_id = self._jobs.get()
                if not future.set_running_or_notify_cancel():
                    continue
                try:
                    future.set_result(
                        self._generate_token(user_agent, locale, timezone_id)
                    )
                except BaseException as exc:
                    # Do not reuse a browser that may be in a bad state.
                    self._close_browser()
                    future.set_exception(exc)
        finally:
            self._close_browser()
            if self._playwright is not None:
                try:
                    self._playwright.stop()
                except Exception:
                    logger.exception("Error stopping Playwright")
                self._playwright = None

    def _get_browser(self):
        """Return the shared browser, (re)launching it when needed. Worker thread only."""
        if self._browser is not None and self._served >= settings.BROWSER_RECYCLE_AFTER:
            self._close_browser()
        if self._browser is not None and not self._browser.is_connected():
            self._close_browser()
        if self._browser is None:
            if self._playwright is None:
                self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            self._served = 0
        return self._browser

    def _close_browser(self):
        browser, self._browser = self._browser, None
        if browser is None:
            return
        try:
            browser.close()
        except Exception:
            logger.exception("Error closing browser")

    def _generate_token(self, user_agent: str, locale: str, timezone_id: str):
        """
        Generate a fresh token in a new context of the shared browser.
        Must run on the worker thread.

        Args:
        - user_agent (str): The user agent string to use for the browser.
        - locale (str): The browser locale to use.
        - timezone_id (str): The browser timezone to use.

        Returns:
        - str: The generated token.
        """
        browser = self._get_browser()
        context = browser.new_context(
            user_agent=user_agent,
            locale=locale,
            timezone_id=timezone_id,
        )
        try:
            page = context.new_page()
            page.goto(self.html_file_path)
            token_element = page.wait_for_selector("body > div")
            token = token_element.inner_text()
        finally:
            context.close()
        self._served += 1
        return token
