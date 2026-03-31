import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOGS_WEBHOOK_URL = os.getenv("LOGS_WEBHOOK_URL")

# Playwright headless mode (default: False for production with Xvfb)
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"

# Token cache TTL in seconds (default: 60)
TOKEN_CACHE_TTL = int(os.getenv("TOKEN_CACHE_TTL", "60"))