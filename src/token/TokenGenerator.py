import os
import fake_useragent
import random
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

        - Sets the path to the HTML file used for token generation.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.html_file_path = f"file:///{current_directory}/token.html"

    def get_token(self):
        """
        Reload Selenium upon token generation for a unique identity.
        
        Get a token from the HTML file.

        Waits for the presence of a specific div element in the HTML file and returns its text content as the token.

        Returns:
        - str: The generated token.
        """
        user_agent = fake_useragent.UserAgent().random
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("--disable-blink-features=AutomationControlled") 
        options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        options.add_experimental_option("useAutomationExtension", False) 
        
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(random.randint(800, 1200), random.randint(600, 900))
        driver.set_window_position(random.randint(0, 800), random.randint(0, 600))
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get(self.html_file_path)

        div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//body/div[1]"))
        )
        return div.text
