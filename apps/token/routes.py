import atexit
import logging
import os
import time

from fake_useragent import FakeUserAgent
from flask import jsonify

from apps.token import blueprint, html_file_path, logger, playwright_context


@blueprint.route("/new_token", methods=["GET"])
def new_token_route():
    """
    Flask route for generating a new token using Playwright.

    Returns:
        Response: JSON response containing the generated token or an error message.
    """
    try:
        start_time = time.time()

        random_useragent = FakeUserAgent().random

        with playwright_context:
            # Create a new browser context with the generated user agent
            my_browser = playwright_context.loop.run_until_complete(
                playwright_context.browser.new_context(user_agent=random_useragent)
            )

            # Create a new page within the browser context
            page = playwright_context.loop.run_until_complete(my_browser.new_page())

            # Navigate to the specified HTML file path
            playwright_context.loop.run_until_complete(page.goto(html_file_path))

            # Wait for the selector "body > div" to appear on the page
            token_element = playwright_context.loop.run_until_complete(
                page.wait_for_selector("body > div")
            )

            # Retrieve the inner text of the selected element as the token
            token = playwright_context.loop.run_until_complete(
                token_element.inner_text()
            )

        logger.info("Token generated in %s seconds" % (time.time() - start_time))
        return jsonify(token), 200

    except Exception as e:
        print(e)
        return (
            jsonify(
                {
                    "status": "erreur",
                    "message": f"An error occurred during the token generation: {e}",
                }
            ),
            500,
        )
