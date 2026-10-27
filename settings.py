import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOGS_WEBHOOK_URL = os.getenv("LOGS_WEBHOOK_URL")

# Hide IP addresses in the logs sent to Discord (default: true). Only the exact
# value "false" shows them, so a typo never exposes users' IPs by accident.
# Console and server logs always keep the full message.
LOGS_WEBHOOK_HIDE_IPS = os.getenv("LOGS_WEBHOOK_HIDE_IPS", "true").strip().lower() != "false"

# Playwright headless mode (default: False for production with Xvfb)
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"

# Active generation deadline in seconds (queue wait and cleanup are excluded).
TOKEN_GENERATION_TIMEOUT_SECONDS = float(os.getenv("TOKEN_GENERATION_TIMEOUT_SECONDS", "120"))
if not 0 < TOKEN_GENERATION_TIMEOUT_SECONDS < float("inf"):
    raise ValueError("TOKEN_GENERATION_TIMEOUT_SECONDS must be a positive finite number")
