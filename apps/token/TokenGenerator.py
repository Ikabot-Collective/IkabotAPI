import asyncio
import logging
import random
from pathlib import Path

from playwright.async_api import Browser, Playwright, async_playwright

import settings

logger = logging.getLogger(__name__)
_CLEANUP_TIMEOUT = 5


def _consume_result(task: asyncio.Task) -> None:
    # A disconnected HTTP client may no longer be awaiting its generation task.
    if not task.cancelled():
        task.exception()


async def _settle(task: asyncio.Task, timeout: float = _CLEANUP_TIMEOUT) -> bool:
    """Wait without cancelling an in-flight Playwright call."""
    done, _ = await asyncio.wait({task}, timeout=timeout)
    if done:
        _consume_result(task)
    else:
        task.add_done_callback(_consume_result)
    return bool(done)


class _BrowserSession:
    """Own one driver/browser; a retired session never modifies its replacement."""

    def __init__(self):
        self.browser: Browser | None = None
        self._playwright: Playwright | None = None
        self._manager = None
        self._closed = False

    async def get_browser(self) -> Browser:
        if self._closed:
            raise RuntimeError("Browser session is closed")
        if self.browser is not None and not self.browser.is_connected():
            await self.browser.close()
            self.browser = None
        if self._closed:
            raise RuntimeError("Browser session is closed")
        if self.browser is None:
            if self._playwright is None:
                self._manager = async_playwright()
                playwright = await self._manager.start()
                if self._closed:
                    await playwright.stop()
                    raise RuntimeError("Browser session is closed")
                self._playwright = playwright
            browser = await self._playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
                timeout=settings.TOKEN_GENERATION_TIMEOUT_SECONDS * 1000,
            )
            if self._closed:
                await browser.close()
                raise RuntimeError("Browser session is closed")
            self.browser = browser
        return self.browser

    async def close(self) -> bool:
        self._closed = True
        browser, self.browser = self.browser, None
        self._playwright = None
        browser_close = asyncio.create_task(browser.close()) if browser else None
        if browser_close:
            await _settle(browser_close)
        if self._manager is None:
            return True

        # Closing the driver also interrupts pending context/page operations.
        driver_close = asyncio.create_task(self._manager.__aexit__())
        if not await _settle(driver_close):
            self._kill_driver()
            if not await _settle(driver_close):
                return False
        if driver_close.exception() is not None:
            self._kill_driver()
            return False
        return browser_close is None or await _settle(browser_close)

    def _kill_driver(self) -> None:
        # Playwright has no public force-stop API. Use its owned Process object
        # only if graceful shutdown hangs; never kill a process by a stale PID.
        try:
            process = self._manager._connection._transport._proc
            if process.returncode is None:
                logger.warning("Force-stopping an unresponsive Playwright driver")
                process.kill()
        except (AttributeError, OSError):
            logger.exception("Unable to force-stop the Playwright driver")


class TokenGenerator:
    """Async, serial token generation with one persistent Chromium per app."""

    def __init__(self, supported_user_agents: list[str]):
        self.supported_user_agents = supported_user_agents
        self.default_locale = "en-GB"
        self.default_timezone_id = "Europe/London"
        self.path = Path(__file__).with_name("token.html").resolve().as_uri()
        self._lock = asyncio.Lock()
        self._shutdown = asyncio.Event()
        self._closed = False
        self._session: _BrowserSession | None = None
        self._requests: set[asyncio.Task] = set()
        self._close_task: asyncio.Task | None = None

    async def get_token(
        self,
        user_agent: str | None = None,
        locale: str | None = None,
        timezone_id: str | None = None,
    ) -> str:
        if self._closed:
            raise RuntimeError("Token generator is closed")
        task = asyncio.create_task(
            self._serve_token(
                user_agent or random.choice(self.supported_user_agents),
                locale or self.default_locale,
                timezone_id or self.default_timezone_id,
            )
        )
        self._requests.add(task)
        task.add_done_callback(self._requests.discard)
        task.add_done_callback(_consume_result)
        # Cancelling a request must not cancel Playwright halfway through a call
        # or release the lock while its context is still in use.
        return await asyncio.shield(task)

    async def _serve_token(self, user_agent, locale, timezone_id) -> str:
        async with self._lock:
            if self._closed:
                raise RuntimeError("Token generator is closed")
            if self._session is None:
                self._session = _BrowserSession()
            session = self._session
            generation = asyncio.create_task(
                self._generate_token(session, user_agent, locale, timezone_id)
            )
            shutdown = asyncio.create_task(self._shutdown.wait())
            try:
                done, _ = await asyncio.wait(
                    {generation, shutdown}, timeout=settings.TOKEN_GENERATION_TIMEOUT_SECONDS,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if generation in done:
                    return generation.result()
                if self._closed:
                    raise RuntimeError("Token generator is closing")
                raise TimeoutError("Token generation timed out")
            except Exception:
                self._session = None
                stopped = await session.close()
                finished = await _settle(generation)
                if not stopped or not finished:
                    # Do not accumulate abandoned drivers or overlap generations.
                    self._closed = True
                    logger.error("Token generator could not stop; restart the API")
                raise
            finally:
                shutdown.cancel()
                await asyncio.gather(shutdown, return_exceptions=True)

    async def _generate_token(self, session, user_agent, locale, timezone_id) -> str:
        browser = await session.get_browser()
        context = await browser.new_context(
            user_agent=user_agent, locale=locale, timezone_id=timezone_id,
        )
        try:
            context.set_default_timeout(settings.TOKEN_GENERATION_TIMEOUT_SECONDS * 1000)
            page = await context.new_page()
            await page.goto(self.path)
            await page.wait_for_selector("body > div")
            token = await page.inner_text("body > div")
        finally:
            await context.close()
        return token

    async def close(self) -> None:
        if self._close_task is None:
            self._closed = True
            self._shutdown.set()
            self._close_task = asyncio.create_task(self._close())
        await asyncio.shield(self._close_task)

    async def _close(self) -> None:
        # Active generation observes shutdown; queued callers reject under the
        # same lock, so none can start a browser after application shutdown.
        if self._requests:
            await asyncio.gather(*self._requests, return_exceptions=True)
        if self._session is not None:
            session, self._session = self._session, None
            if not await session.close():
                logger.error("Playwright did not shut down cleanly")
