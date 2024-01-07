import atexit
import logging
import os

from flask import Blueprint

from apps.token.PlaywrightContext import PlaywrightContext

logger = logging.getLogger()

playwright_context = PlaywrightContext()

# Path to the HTML file for token generation
html_file_path = f"file:///{os.path.dirname(os.path.abspath(__file__))}/token.html"

blueprint = Blueprint("token_blueprint", __name__, url_prefix="")


def close_playwright():
    logger.info("Stopping Playwright instance...")
    playwright_context.stop()
    logger.info("Playwright instance stopped.")


atexit.register(close_playwright)
