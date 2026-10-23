import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOGS_WEBHOOK_URL = os.getenv("LOGS_WEBHOOK_URL")

# Playwright headless mode (default: False for production with Xvfb)
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"

# Active generation deadline in seconds (queue wait and cleanup are excluded).
TOKEN_GENERATION_TIMEOUT_SECONDS = float(os.getenv("TOKEN_GENERATION_TIMEOUT_SECONDS", "120"))
if not 0 < TOKEN_GENERATION_TIMEOUT_SECONDS < float("inf"):
    raise ValueError("TOKEN_GENERATION_TIMEOUT_SECONDS must be a positive finite number")
