import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TokenGenerator:
    """
    TokenGenerator class for generating tokens using Selenium.

    This class initializes a Selenium WebDriver with a headless Chrome browser and provides a method to retrieve tokens
    from game1.js.

    Usage:
    ```
    token_generator = TokenGenerator()
    token = token_generator.get_token()
    ```
    """

    def __init__(self):
        """
        Initialize TokenGenerator.

        - Initializes the Selenium WebDriver with a headless Chrome browser.
        - Sets the path to the HTML file used for token generation.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.html_file_path = f"file:///{current_directory}/token.html"
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

    def get_token(self):
        """
        Get a token from the HTML file.

        Waits for the presence of a specific div element in the HTML file and returns its text content as the token.

        Returns:
        - str: The generated token.
        """
        self.driver.get(self.html_file_path)

        div = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//body/div[1]"))
        )

        return div.text
