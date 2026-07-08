import logging
import os
import random
import threading

from playwright.sync_api import sync_playwright

import settings

logger = logging.getLogger(__name__)

DEFAULT_LOCALE = "en-GB"
DEFAULT_TIMEZONE_ID = "Europe/London"


class TokenGenerator:
    """
    TokenGenerator class for generating tokens using Playwright.

    Uses a threading lock to prevent concurrent Playwright subprocess spawning
    (which causes "Racing with another loop" crashes with uvloop). Each call
    generates a fresh blackbox token.

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
        self._lock = threading.Lock()

    def get_token(
        self,
        user_agent: str = None,
        locale: str = None,
        timezone_id: str = None,
    ):
        """
        Generate a fresh blackbox token.

        A threading lock serializes Playwright calls to prevent uvloop race
        conditions when multiple requests arrive concurrently. When no
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

        with self._lock:
            return self._generate_token(
                effective_ua,
                effective_locale,
                effective_timezone_id,
            )

    def _generate_token(self, user_agent: str, locale: str, timezone_id: str):
        """
        Launch Playwright to generate a fresh token.

        Args:
        - user_agent (str): The user agent string to use for the browser.
        - locale (str): The browser locale to use.
        - timezone_id (str): The browser timezone to use.

        Returns:
        - str: The generated token.
        """
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            context = browser.new_context(
                user_agent=user_agent,
                locale=locale,
                timezone_id=timezone_id,
            )
            page = context.new_page()
            page.goto(self.html_file_path)
            token_element = page.wait_for_selector("body > div")
            token = token_element.inner_text()
            browser.close()
        return token
