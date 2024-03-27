import os

from fake_useragent import FakeUserAgent
from playwright.sync_api import sync_playwright


class TokenGenerator:
    """
    TokenGenerator class for generating tokens using Playwright.

    Usage:
    ```
    token_generator = TokenGenerator()
    token = token_generator.get_token()
    ```
    """

    def __init__(self):
        """
        Initialize TokenGenerator.

        - Sets the path to the HTML file used for token generation.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.html_file_path = f"file:///{current_directory}/token.html"
        self.user_agents = {}

    def get_token(self, user_id):
        """
        Get a token from the HTML file.
        
        Checks the dictionary for a user agent for the given user_id.
        If a match is not found, generates a new random user agent and saves it in the dictionary.
        If a match is found, uses the saved user agent from the dictionary for that user_id.

        Waits for the presence of a specific div element in the HTML file and returns its text content as the token.

        Returns:
        - str: The generated token.
        """
        if user_id not in self.user_agents:
            self.user_agents[user_id] = FakeUserAgent().random
        random_useragent = self.user_agents[user_id]
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(user_agent=random_useragent)
            page = context.new_page()
            page.goto(self.html_file_path)
            token_element = page.wait_for_selector("body > div")
            token = token_element.inner_text()
            browser.close()
        return token
