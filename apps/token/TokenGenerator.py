import logging
import os
import queue
import random
import signal
import threading
import time
from concurrent.futures import Future

from playwright.sync_api import sync_playwright

import settings

logger = logging.getLogger(__name__)

# Queued after the last job to tell the worker thread to shut down.
_STOP = object()

DEFAULT_LOCALE = "en-GB"
DEFAULT_TIMEZONE_ID = "Europe/London"


class TokenGenerator:
    """
    TokenGenerator class for generating tokens using Playwright.

    A single dedicated worker thread owns the Playwright instance and a
    long-lived Chromium browser. Requests are queued (FIFO) and served one at a
    time, which prevents concurrent Playwright subprocess spawning (the
    "Racing with another loop" crashes with uvloop) and avoids paying the
    Chromium start-up cost for every token. Each token still gets its own fresh
    browser context, so no state is shared between tokens. The browser is
    relaunched every `BROWSER_RECYCLE_AFTER` tokens. After any failure both the
    browser and the Playwright driver are discarded and recreated on the next
    request, so a crashed driver cannot leave the generator stuck. Call
    `close()` to stop the worker and release the browser (the app does this on
    shutdown).

    A Playwright call can block forever if the driver process dies mid-request
    (no exception is raised in the worker thread). A watchdog therefore fails
    any token that runs longer than `TOKEN_JOB_TIMEOUT` seconds, kills the
    driver, abandons the stuck thread and starts a fresh worker on the same
    queue.

    Usage:
    ```
    token_generator = TokenGenerator(supported_user_agents=["User Agent 1", "User Agent 2"])
    token = token_generator.get_token()
    ```
    """

    def __init__(self, supported_user_agents):
        """
        Initialize TokenGenerator.

        Args:
        - supported_user_agents: List of supported user agent strings.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.html_file_path = f"file:///{current_directory}/token.html"
        self.supported_user_agents = supported_user_agents
        self.default_locale = DEFAULT_LOCALE
        self.default_timezone_id = DEFAULT_TIMEZONE_ID
        self._jobs = queue.Queue()
        self._worker = None
        self._playwright = None
        self._browser = None
        self._served = 0
        self._worker_lock = threading.Lock()
        self._closed = False
        self._closed_event = threading.Event()
        self._generation = 0
        self._current = None  # (future, started_at) of the job being processed
        self._driver_pid = None
        self._watchdog = None

    def _ensure_worker_locked(self):
        if self._worker is None or not self._worker.is_alive():
            self._start_worker_locked()
        if self._watchdog is None or not self._watchdog.is_alive():
            self._watchdog = threading.Thread(
                target=self._watchdog_loop, name="token-watchdog", daemon=True
            )
            self._watchdog.start()

    def _start_worker_locked(self):
        self._worker = threading.Thread(
            target=self._worker_loop,
            args=(self._generation,),
            name="token-worker",
            daemon=True,
        )
        self._worker.start()

    def get_token(
        self,
        user_agent: str = None,
        locale: str = None,
        timezone_id: str = None,
    ):
        """
        Generate a fresh blackbox token.

        Requests are queued and served one at a time by a worker thread that
        keeps a single browser open, which prevents uvloop race conditions
        when multiple requests arrive concurrently. When no
        user_agent is provided, a random one from the supported list is used.
        Empty locale and timezone values fall back to configured defaults.

        Args:
        - user_agent (str, optional): The user agent string to use for the browser.
        - locale (str, optional): Browser locale to use for token generation.
        - timezone_id (str, optional): Browser timezone to use for token generation.

        Returns:
        - str: The generated token.
        """
        effective_ua = user_agent if user_agent else random.choice(self.supported_user_agents)
        effective_locale = locale if locale else self.default_locale
        effective_timezone_id = (
            timezone_id if timezone_id else self.default_timezone_id
        )

        future = Future()
        with self._worker_lock:
            if self._closed:
                raise RuntimeError("TokenGenerator is closed")
            self._ensure_worker_locked()
            self._jobs.put(
                (future, effective_ua, effective_locale, effective_timezone_id)
            )
        return future.result()

    def close(self, timeout: float = 30):
        """
        Stop the worker thread and release the browser and Playwright.

        Requests already queued are still served first; new requests are
        rejected. Safe to call more than once.
        """
        with self._worker_lock:
            if self._closed:
                return
            self._closed = True
            self._closed_event.set()
            worker = self._worker
            if worker is not None and worker.is_alive():
                self._jobs.put(_STOP)
        if worker is not None:
            worker.join(timeout)

    def _worker_loop(self, generation):
        """Serve queued token requests, keeping one browser open between them."""
        try:
            while generation == self._generation:
                job = self._jobs.get()
                if job is _STOP:
                    break
                future, user_agent, locale, timezone_id = job
                if not future.set_running_or_notify_cancel():
                    continue
                self._current = (future, time.monotonic())
                try:
                    token = self._generate_token(user_agent, locale, timezone_id)
                except BaseException as exc:
                    with self._worker_lock:
                        if generation != self._generation:
                            return  # abandoned by the watchdog; its state is gone
                        # Do not reuse a browser or driver that may be in a bad
                        # state. Closing a browser whose driver died can block
                        # forever, so instead of cleaning up in this thread the
                        # driver is killed and a fresh worker takes over.
                        self._replace_worker_locked()
                    _set_exception(future, exc)
                    return
                else:
                    if generation != self._generation:
                        return
                    self._current = None
                    _set_result(future, token)
        finally:
            if generation == self._generation:
                self._reset()

    def _watchdog_loop(self):
        """Recover from a worker blocked inside a Playwright call."""
        while not self._closed_event.wait(1.0):
            current = self._current
            if current is None:
                continue
            elapsed = time.monotonic() - current[1]
            if elapsed > settings.TOKEN_JOB_TIMEOUT:
                self._abandon_worker(current, f"exceeded {settings.TOKEN_JOB_TIMEOUT}s")
            elif elapsed > 1 and not _process_alive(self._driver_pid):
                # A dead driver never answers, so there is no point in waiting.
                self._abandon_worker(current, "driver process died")

    def _abandon_worker(self, current, reason):
        with self._worker_lock:
            if self._closed or self._current is not current:
                return
            logger.error("Token generation failed (%s); restarting the browser worker", reason)
            self._replace_worker_locked()
        _set_exception(
            current[0], TimeoutError(f"Token generation failed: {reason}")
        )

    def _replace_worker_locked(self):
        """Kill the driver, forget this worker's state and start a fresh worker.

        The previous worker thread may be blocked inside Playwright forever; it
        is left behind (it is a daemon thread) and ignores everything from now
        on because its generation is stale. Queued requests are picked up by
        the new worker.
        """
        self._generation += 1
        self._current = None
        self._kill_driver()
        self._browser = None
        self._playwright = None
        self._served = 0
        self._start_worker_locked()

    def _kill_driver(self):
        pid, self._driver_pid = self._driver_pid, None
        if pid is None:
            return
        try:
            # Windows has no SIGKILL; os.kill() terminates the process there.
            os.kill(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
        except OSError:
            pass

    def _reset(self):
        """Close the browser and stop the Playwright driver; both are recreated on demand."""
        self._close_browser()
        playwright, self._playwright = self._playwright, None
        self._driver_pid = None
        if playwright is not None:
            try:
                playwright.stop()
            except Exception:
                logger.exception("Error stopping Playwright")

    def _get_browser(self):
        """Return the shared browser, (re)launching it when needed. Worker thread only."""
        if self._browser is not None and self._served >= settings.BROWSER_RECYCLE_AFTER:
            self._close_browser()
        if self._browser is not None and not self._browser.is_connected():
            self._close_browser()
        if self._browser is None:
            if self._playwright is None:
                self._playwright = sync_playwright().start()
                self._driver_pid = _driver_pid(self._playwright)
            self._browser = self._playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            self._served = 0
        return self._browser

    def _close_browser(self):
        browser, self._browser = self._browser, None
        if browser is None:
            return
        try:
            browser.close()
        except Exception:
            logger.exception("Error closing browser")

    def _generate_token(self, user_agent: str, locale: str, timezone_id: str):
        """
        Generate a fresh token in a new context of the shared browser.
        Must run on the worker thread.

        Args:
        - user_agent (str): The user agent string to use for the browser.
        - locale (str): The browser locale to use.
        - timezone_id (str): The browser timezone to use.

        Returns:
        - str: The generated token.
        """
        browser = self._get_browser()
        context = browser.new_context(
            user_agent=user_agent,
            locale=locale,
            timezone_id=timezone_id,
        )
        try:
            page = context.new_page()
            page.goto(self.html_file_path)
            token_element = page.wait_for_selector("body > div")
            token = token_element.inner_text()
        finally:
            context.close()
        self._served += 1
        return token


def _set_result(future, value):
    if not future.done():
        future.set_result(value)


def _set_exception(future, exc):
    if not future.done():
        future.set_exception(exc)


def _driver_pid(playwright):
    """PID of the Playwright driver process, or None if it cannot be found."""
    try:
        return playwright._impl_obj._connection._transport._proc.pid
    except AttributeError:
        return None


def _process_alive(pid):
    """False only when `pid` is known to be gone (or a zombie). Linux only."""
    if pid is None:
        return True
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return not os.path.isdir("/proc")
    except (OSError, IndexError):
        return True
