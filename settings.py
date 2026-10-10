import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOGS_WEBHOOK_URL = os.getenv("LOGS_WEBHOOK_URL")

# Playwright headless mode (default: False for production with Xvfb)
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"

# Relaunch the shared Chromium after this many tokens to bound memory growth
BROWSER_RECYCLE_AFTER = int(os.getenv("BROWSER_RECYCLE_AFTER", "100"))
