import logging
import os
import random
import threading

from playwright.sync_api import sync_playwright

import settings

logger = logging.getLogger(__name__)


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
        self._lock = threading.Lock()

    def get_token(self, user_agent: str = None):
        """
        Generate a fresh blackbox token.

        A threading lock serializes Playwright calls to prevent uvloop race
        conditions when multiple requests arrive concurrently. When no
        user_agent is provided, a random one from the supported list is used.

        Args:
        - user_agent (str, optional): The user agent string to use for the browser.

        Returns:
        - str: The generated token.
        """
        effective_ua = user_agent if user_agent else random.choice(self.supported_user_agents)

        with self._lock:
            return self._generate_token(effective_ua)

    def _generate_token(self, user_agent: str):
        """
        Launch Playwright to generate a fresh token.

        Args:
        - user_agent (str): The user agent string to use for the browser.

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
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            page.goto(self.html_file_path)
            token_element = page.wait_for_selector("body > div")
            token = token_element.inner_text()
            browser.close()
        return token
