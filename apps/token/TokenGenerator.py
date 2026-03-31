import logging
import os
import threading
import time

from fake_useragent import FakeUserAgent
from playwright.sync_api import sync_playwright

import settings

logger = logging.getLogger(__name__)


class TokenGenerator:
    """
    TokenGenerator class for generating tokens using Playwright.

    Uses a threading lock to prevent concurrent Playwright subprocess spawning
    (which causes "Racing with another loop" crashes with uvloop), and an
    in-memory cache with configurable TTL to reduce Playwright invocations.

    Usage:
    ```
    token_generator = TokenGenerator(supported_user_agents=["User Agent 1", "User Agent 2"])
    token = token_generator.get_token()
    ```
    """

    def __init__(self, supported_user_agents, cache_ttl=None):
        """
        Initialize TokenGenerator.

        Args:
        - supported_user_agents: List of supported user agent strings.
        - cache_ttl: Cache time-to-live in seconds. Defaults to settings.TOKEN_CACHE_TTL.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.html_file_path = f"file:///{current_directory}/token.html"
        self.supported_user_agents = supported_user_agents
        self._lock = threading.Lock()
        self._cache = {}
        self._cache_ttl = cache_ttl if cache_ttl is not None else settings.TOKEN_CACHE_TTL

    def get_token(self, user_agent: str = None):
        """
        Get a token, returning a cached value when available.

        When a user_agent is provided, tokens are cached per user_agent with a
        configurable TTL. Without user_agent (legacy), a random UA is used each
        time and the result is not cached.

        A threading lock serializes Playwright calls to prevent uvloop race
        conditions when multiple requests arrive concurrently.

        Args:
        - user_agent (str, optional): The user agent string to use for the browser.

        Returns:
        - str: The generated token.
        """
        if user_agent:
            cached = self._cache.get(user_agent)
            if cached and cached[1] > time.time():
                logger.info("Token cache hit for user_agent (TTL %.0fs remaining)", cached[1] - time.time())
                return cached[0]

        with self._lock:
            if user_agent:
                cached = self._cache.get(user_agent)
                if cached and cached[1] > time.time():
                    return cached[0]

            token = self._generate_token(user_agent)

            if user_agent:
                self._cache[user_agent] = (token, time.time() + self._cache_ttl)

            return token

    def _generate_token(self, user_agent: str = None):
        """
        Launch Playwright to generate a fresh token.

        Args:
        - user_agent (str, optional): The user agent string to use for the browser.

        Returns:
        - str: The generated token.
        """
        with sync_playwright() as playwright:
            if user_agent and user_agent in self.supported_user_agents:
                playwright_useragent = user_agent
            else:
                playwright_useragent = FakeUserAgent().random
            browser = playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            context = browser.new_context(user_agent=playwright_useragent)
            page = context.new_page()
            page.goto(self.html_file_path)
            token_element = page.wait_for_selector("body > div")
            token = token_element.inner_text()
            browser.close()
        return token
