import asyncio
import logging
import logging.handlers
import queue
import re
import threading
import time
from contextlib import asynccontextmanager

import coloredlogs
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import settings
from apps import __version__
from apps.decaptcha.routes import router as decaptcha_router
from apps.home.routes import router as home_router
from apps.token import supported_user_agents
from apps.token.TokenGenerator import TokenGenerator
from apps.token.routes import router as token_router

logger = logging.getLogger(__name__)


# IPv4 and IPv6 addresses, masked in the logs sent to Discord.
_IP_ADDRESS = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    r"|\b(?:[0-9a-fA-F]{0,4}:){3,7}[0-9a-fA-F]{1,4}\b"
)


class HideIPsFormatter(logging.Formatter):
    """Mask IP addresses in the formatted text only, leaving the record intact."""

    def format(self, record):
        return _IP_ADDRESS.sub("x.x.x.x", super().format(record))


# Loggers that run while a message is being sent to Discord. Forwarding their
# records (e.g. "Webhook rate limited") would send more messages, endlessly.
_DISCORD_INTERNAL_LOGGERS = ("discord_webhook", "discord_logging", "urllib3", "requests")


def _is_discord_internal(record: logging.LogRecord) -> bool:
    return any(
        record.name == name or record.name.startswith(name + ".")
        for name in _DISCORD_INTERNAL_LOGGERS
    )


class BackgroundHandler(logging.handlers.QueueHandler):
    """Run a slow handler on a background thread.

    Logging also happens on the event loop (access logs, async routes, token
    generation). The Discord handler makes blocking HTTP requests and sleeps when
    Discord rate limits it, which froze the loop and Playwright with it. Here a
    log call only puts the record in a bounded queue. When the queue is full the
    record is dropped, so a slow or unreachable Discord never blocks the API and
    never grows memory.
    """

    def __init__(self, target: logging.Handler, maxsize: int = 1000):
        super().__init__(queue.Queue(maxsize))
        self.target = target
        self.dropped = 0
        self.setLevel(target.level)
        self.addFilter(lambda record: not _is_discord_internal(record))
        self._thread = threading.Thread(
            target=self._forward, name="discord-logs", daemon=True
        )
        self._thread.start()

    def enqueue(self, record):
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            self.dropped += 1

    def _forward(self):
        while (record := self.queue.get()) is not None:
            try:
                self.target.handle(record)
            except Exception:
                self.target.handleError(record)

    def close(self, timeout: float = 5):
        """Stop the thread, giving queued records up to `timeout` seconds to be sent."""
        if self._thread.is_alive():
            deadline = time.monotonic() + timeout
            try:
                self.queue.put(None, timeout=timeout)
            except queue.Full:
                pass
            self._thread.join(max(0.0, deadline - time.monotonic()))
            if self._thread.is_alive():
                # Discord is too slow: drop the rest, so the thread stops after
                # the message it is sending now.
                with self.queue.mutex:
                    self.queue.queue.clear()
                    self.queue.not_full.notify_all()
                self.queue.put_nowait(None)
        self.target.close()
        super().close()


_discord_logs: BackgroundHandler | None = None


def close_discord_logs(timeout: float = 5):
    global _discord_logs
    handler, _discord_logs = _discord_logs, None
    if handler is not None:
        logging.getLogger().removeHandler(handler)
        handler.close(timeout)


def setup_logger():
    """
    Set up the root logger with a Discord handler and colored console output.
    This ensures all modules using logging.getLogger() will benefit from the configuration.
    """
    global _discord_logs
    root_logger = logging.getLogger()

    # Clear existing handlers to avoid duplicates
    close_discord_logs(timeout=0)
    root_logger.handlers.clear()

    # Install coloredlogs only on root logger
    coloredlogs.install(level=logging.INFO, logger=root_logger)

    # Disable uvicorn's default loggers to avoid duplicate output
    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.error").handlers.clear()

    # Make uvicorn loggers propagate to root (so they use our handlers)
    logging.getLogger("uvicorn").propagate = True
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("uvicorn.error").propagate = True

    if settings.LOGS_WEBHOOK_URL is not None and settings.LOGS_WEBHOOK_URL != "":
        from discord_logging.handler import DiscordHandler

        # Define format for logs. Only the Discord copy hides users' IPs; the
        # console and server logs keep the full message.
        formatter_class = (
            HideIPsFormatter if settings.LOGS_WEBHOOK_HIDE_IPS else logging.Formatter
        )
        discord_format = formatter_class("%(name)s - %(message)s")

        discord_handler = DiscordHandler("Ikabot API", settings.LOGS_WEBHOOK_URL)
        discord_handler.setFormatter(discord_format)

        # Send INFO and above to Discord
        discord_handler.setLevel(logging.INFO)

        # Never send from the calling thread: it may be the event loop.
        _discord_logs = BackgroundHandler(discord_handler)
        root_logger.addHandler(_discord_logs)

    root_logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logger()
    # The service belongs to this lifespan/event loop. Chromium starts lazily on
    # the first token and remains available until a failure or shutdown.
    token_generator = TokenGenerator(supported_user_agents)
    app.state.token_generator = token_generator
    logger.info("Ikabot API ready!")
    try:
        yield
    finally:
        logger.info("Ikabot API shutting down")
        await token_generator.close()
        del app.state.token_generator
        await asyncio.to_thread(close_discord_logs)


app = FastAPI(
    title="Ikabot API",
    description="API for Ikabot captcha solving and token generation",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="apps/templates/static"), name="static")

# Include routers
app.include_router(home_router)
app.include_router(token_router)
app.include_router(decaptcha_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5005,
        reload=True,
        log_level="info"
    )
