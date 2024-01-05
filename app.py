import asyncio
import os
import time

from fake_useragent import FakeUserAgent
from flask import Flask, jsonify
from playwright.async_api import async_playwright


def create_app(config):
    loop = asyncio.get_event_loop()

    app = Flask(__name__)
    app.config.from_object(config)

    playwright = loop.run_until_complete(async_playwright().start())
    browser = loop.run_until_complete(playwright.chromium.launch(headless=True))

    current_directory = os.path.dirname(os.path.abspath(__file__))
    html_file_path = f"file:///{current_directory}/src/token/token.html"

    @app.route("/new_token", methods=["GET"])
    def new_token_route():
        try:
            start_time = time.time()

            random_useragent = FakeUserAgent().random
            my_browser = loop.run_until_complete(
                browser.new_context(user_agent=random_useragent)
            )
            page = loop.run_until_complete(my_browser.new_page())
            loop.run_until_complete(page.goto(html_file_path))
            token_element = loop.run_until_complete(
                page.wait_for_selector("body > div")
            )
            token = loop.run_until_complete(token_element.inner_text())
            browser.close()

            print("Token generated in %s seconds" % (time.time() - start_time))
            return jsonify(token), 200

        except Exception as e:
            print(e)
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"An error occurred during the token generation: {e}",
                    }
                ),
                500,
            )

    return app


if __name__ == "__main__":
    app = create_app({})
    app.run()
