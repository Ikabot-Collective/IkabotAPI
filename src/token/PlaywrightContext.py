import asyncio

from playwright.async_api import async_playwright


class PlaywrightContext:
    """
    A context manager for managing Playwright resources.

    Usage:
    ```python
    with PlaywrightContext() as playwright_context:
        # Perform Playwright operations within this context
    ```
    """

    def __init__(self):
        """
        Initializes a new instance of the PlaywrightContext.

        This constructor creates a new asyncio event loop, sets it as the current loop,
        and initializes the Playwright instance with a Chromium browser.
        """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.playwright = self.loop.run_until_complete(async_playwright().start())
        self.browser = self.loop.run_until_complete(
            self.playwright.chromium.launch(headless=True)
        )

    def __enter__(self):
        """
        Enters the context and returns the PlaywrightContext instance.

        Returns:
            PlaywrightContext: The instance of the PlaywrightContext.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exits the context.

        This method is called when exiting the context. Currently, no cleanup is performed
        here as cleanup is handled in the main application.
        """
        pass  # No cleanup required

    def close_and_stop(self):
        """
        Closes the browser and stops the Playwright instance.

        This method should be called when you want to clean up resources.
        """
        if self.browser:
            self.loop.run_until_complete(self.browser.close())
            self.browser = None  # Set browser to None after closing
        if self.playwright:
            self.loop.run_until_complete(self.playwright.stop())
            self.playwright = None  # Set playwright to None after stopping
        self.loop.close()
