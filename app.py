import os
import signal
import time

from fake_useragent import FakeUserAgent
from flask import Flask, jsonify

from src.token.PlaywrightContext import PlaywrightContext

# Initialize a global PlaywrightContext instance
playwright_context = PlaywrightContext()


def create_app(config):
    """
    Factory function to create the Flask application.

    Args:
        config: Configuration object for Flask application.

    Returns:
        Flask: The created Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config)

    # Path to the HTML file for token generation
    html_file_path = (
        f"file:///{os.path.dirname(os.path.abspath(__file__))}/src/token/token.html"
    )

    @app.route("/new_token", methods=["GET"])
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

            print("Token generated in %s seconds" % (time.time() - start_time))
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

    @app.teardown_appcontext
    def teardown_context():
        """
        Flask teardown handler to close and stop Playwright resources.

        This function is called when the application context is popped.
        """
        playwright_context.close_and_stop()

    return app


def close_playwright_resources(signal, frame):
    """
    Signal handler to close and stop Playwright resources.

    Args:
        signal: Signal number.
        frame: Signal frame.
    """
    playwright_context.close_and_stop()


if __name__ == "__main__":
    app = create_app({})

    # Register the close_playwright_resources function for the termination signal
    signal.signal(signal.SIGTERM, close_playwright_resources)
    signal.signal(signal.SIGINT, close_playwright_resources)

    app.run()
