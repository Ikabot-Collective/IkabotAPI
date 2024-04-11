import json
import os

from fake_useragent import FakeUserAgent
from playwright.sync_api import sync_playwright


class TokenGenerator:
    """
    TokenGenerator class for generating tokens using Playwright.

    Usage:
    ```
    token_generator = TokenGenerator(supported_user_agents=["User Agent 1", "User Agent 2"])
    token = token_generator.get_token()
    ```
    """

    def __init__(self, supported_user_agents):
        """
        Initialize TokenGenerator.

        - Sets the path to the HTML file used for token generation.
        - Sets the supported user agents.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.html_file_path = f"file:///{current_directory}/token.html"
        self.supported_user_agents = supported_user_agents

    def get_token(self, user_agent: str = None):
        """
        Get a token from the HTML file.

        This method waits for the presence of a specific div element in the HTML file and returns its text content as the token.

        Args:
        - user_agent (str, optional): The user agent string to use for the browser. If not provided, a random user agent will be used.

        Returns:
        - str: The generated token.
        """
        with sync_playwright() as playwright:
            if user_agent and user_agent in self.supported_user_agents:
                playwright_useragent = user_agent
            else:
                playwright_useragent = FakeUserAgent().random
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(user_agent=playwright_useragent)
            page = context.new_page()
            page.goto(self.html_file_path)
            token_element = page.wait_for_selector("body > div")
            token = token_element.inner_text()
            browser.close()
        return token
