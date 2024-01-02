import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


current_directory = os.path.dirname(os.path.abspath(__file__))

html_file_path = f"file:///{current_directory}/getToken.html"

options = webdriver.FirefoxOptions()
options.add_argument("--headless")

driver = webdriver.Firefox(options=options)

def getToken():

    driver.get(html_file_path)

    div = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//body/div[1]"))
    )

    return div.text
