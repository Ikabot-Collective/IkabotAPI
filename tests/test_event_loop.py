"""The event loop serves every route and drives Playwright, so nothing may block it.

In production a rate-limited Discord webhook slept inside logging calls made on
the loop. Playwright could not answer in time, the browser could not be stopped
and the token generator stayed closed until the API was restarted.
"""
import asyncio
import logging
import os
import time

import httpx
import pytest
from pytest_mock import MockerFixture

import main
import settings
from main import app
from tests.test_token_generator import block_first_token, wait_for_blocked_page
from tests.token_validator import verify_token_format

pytestmark = pytest.mark.asyncio

IMG = os.path.join(os.path.dirname(__file__), "img")


@pytest.fixture
def slow_discord(mocker: MockerFixture):
    """A Discord webhook that is rate limited: every message takes a while."""
    mocker.patch("settings.LOGS_WEBHOOK_URL", "https://example.com/webhook")
    mocker.patch(
        "discord_logging.handler.DiscordHandler.emit",
        lambda self, record: time.sleep(1),
    )
    yield
    main.close_discord_logs(timeout=0)
    logging.getLogger().handlers.clear()


async def _max_loop_lag(stop: asyncio.Event) -> float:
    worst = 0.0
    while not stop.is_set():
        start = time.perf_counter()
        await asyncio.sleep(0.01)
        worst = max(worst, time.perf_counter() - start - 0.01)
    return worst


def _image(name):
    with open(os.path.join(IMG, name), "rb") as f:
        return f.read()


async def test_routes_and_logs_never_block_the_event_loop(slow_discord):
    async with app.router.lifespan_context(app):
        stop = asyncio.Event()
        lag = asyncio.create_task(_max_loop_lag(stop))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Uvicorn writes its access log from the event loop.
            logging.getLogger("uvicorn.access").info('1.2.3.4 - "GET /health" 200')
            lobby = await client.post("/v1/decaptcha/lobby", files={
                "text_image": ("t.png", _image("login_text1.png"), "image/png"),
                "icons_image": ("i.png", _image("login_icons1.png"), "image/png"),
            })
            pirate = await client.post("/v1/decaptcha/pirate", files={
                "image": ("p.png", _image("pirate1.png"), "image/png"),
            })
            token = await client.get("/v1/token")
        stop.set()
        assert lobby.json() == 3
        assert pirate.status_code == 200
        verify_token_format(token.json())
        assert await lag < 0.5


async def test_token_generator_survives_a_slow_discord_during_a_timeout(
    slow_discord, monkeypatch
):
    """The production incident: a token times out while logs flood a slow Discord."""
    async with app.router.lifespan_context(app):
        generator = app.state.token_generator
        await generator.get_token()
        started, pages = await block_first_token(generator, monkeypatch)
        monkeypatch.setattr(settings, "TOKEN_GENERATION_TIMEOUT_SECONDS", 1)
        stop = asyncio.Event()

        async def access_logs():
            while not stop.is_set():
                logging.getLogger("uvicorn.access").info('"POST /v1/decaptcha/pirate" 200')
                await asyncio.sleep(0.05)

        chatter = asyncio.create_task(access_logs())
        try:
            request = asyncio.create_task(generator.get_token())
            await wait_for_blocked_page(started, pages)
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(request, 30)
            assert not generator.closed
            verify_token_format(await asyncio.wait_for(generator.get_token(), 30))
        finally:
            stop.set()
            await chatter


async def test_health_reports_a_closed_token_generator():
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            assert (await client.get("/health")).json()["status"] == "healthy"
            # The state left by a browser that could not be stopped.
            app.state.token_generator._closed = True
            health = await client.get("/health")
            assert health.status_code == 503
            assert health.json()["status"] == "unhealthy"
            app.state.token_generator._closed = False


async def test_failed_stop_closes_the_generator_and_health_reports_it(monkeypatch):
    from apps.token.TokenGenerator import _BrowserSession

    original_close = _BrowserSession.close

    async def close_that_cannot_confirm(self):
        await original_close(self)
        return False

    async with app.router.lifespan_context(app):
        generator = app.state.token_generator
        await generator.get_token()
        started, pages = await block_first_token(generator, monkeypatch)
        monkeypatch.setattr(settings, "TOKEN_GENERATION_TIMEOUT_SECONDS", 1)
        monkeypatch.setattr(_BrowserSession, "close", close_that_cannot_confirm)
        request = asyncio.create_task(generator.get_token())
        await wait_for_blocked_page(started, pages)
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(request, 30)
        assert generator.closed
        with pytest.raises(RuntimeError, match="closed"):
            await generator.get_token()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            assert (await client.get("/health")).status_code == 503
