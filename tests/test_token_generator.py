import asyncio
import importlib
import signal
import sys
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

import settings
from apps.token import supported_user_agents
from apps.token.TokenGenerator import TokenGenerator
from tests.token_validator import verify_token_format

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def token_generator():
    generator = TokenGenerator(supported_user_agents)
    yield generator
    await generator.close()


@pytest.mark.parametrize("user_agent", [None, "", supported_user_agents[0]])
async def test_get_token_returns_unique_valid_tokens(token_generator, user_agent):
    tokens = [await token_generator.get_token(user_agent) for _ in range(5)]
    assert len(set(tokens)) == len(tokens)
    for token in tokens:
        verify_token_format(token)


@pytest.mark.parametrize(
    "params, expected",
    [({}, ("en-GB", "Europe/London")),
     ({"locale": "es-ES", "timezone_id": "Europe/Madrid"},
      ("es-ES", "Europe/Madrid"))],
)
async def test_get_token_passes_context_parameters(token_generator, params, expected):
    captured = []

    async def generate(session, user_agent, locale, timezone_id):
        captured.append((user_agent, locale, timezone_id))
        return "token"

    token_generator._generate_token = generate
    assert await token_generator.get_token("Test User Agent", **params) == "token"
    assert captured == [("Test User Agent", *expected)]


async def test_reuses_browser_with_a_fresh_context_per_token(token_generator):
    await token_generator.get_token()
    browser = token_generator._session.browser
    contexts = []
    original_new_context = browser.new_context

    async def new_context(**kwargs):
        context = await original_new_context(**kwargs)
        assert await context.cookies() == []
        await context.add_cookies([{
            "name": "previous-token", "value": "secret", "url": "https://example.com",
        }])
        contexts.append((context, kwargs))
        return context

    browser.new_context = new_context
    first = await token_generator.get_token(
        supported_user_agents[0], locale="es-AR",
        timezone_id="America/Argentina/Buenos_Aires",
    )
    second = await token_generator.get_token(supported_user_agents[1])
    assert first != second
    assert token_generator._session.browser is browser
    assert len(contexts) == 2 and contexts[0][0] is not contexts[1][0]
    assert [kwargs for _, kwargs in contexts] == [
        {"user_agent": supported_user_agents[0], "locale": "es-AR",
         "timezone_id": "America/Argentina/Buenos_Aires"},
        {"user_agent": supported_user_agents[1], "locale": "en-GB",
         "timezone_id": "Europe/London"},
    ]
    assert browser.contexts == []


async def test_recovers_after_a_failed_token(token_generator):
    await token_generator.get_token()
    session = token_generator._session

    async def broken_new_context(**kwargs):
        raise RuntimeError("boom")

    session.browser.new_context = broken_new_context
    with pytest.raises(RuntimeError, match="boom"):
        await token_generator.get_token()
    verify_token_format(await token_generator.get_token())
    assert token_generator._session is not session


async def test_recovers_after_browser_disconnects(token_generator):
    await token_generator.get_token()
    browser = token_generator._session.browser
    await browser.close()
    verify_token_format(await token_generator.get_token())
    assert token_generator._session.browser is not browser


def driver_process(generator):
    return generator._session._manager._connection._transport._proc


async def test_recovers_after_the_driver_dies(token_generator):
    await token_generator.get_token()
    process = driver_process(token_generator)
    process.kill()
    await process.wait()
    try:
        token = await asyncio.wait_for(token_generator.get_token(), 15)
    except Exception:
        token = await asyncio.wait_for(token_generator.get_token(), 15)
    verify_token_format(token)
    assert driver_process(token_generator) is not process


async def block_first_token(generator, monkeypatch):
    """Block a real Playwright RPC until its browser/driver is closed."""
    original = generator._generate_token
    started = asyncio.Event()
    pages = []

    async def generate(session, user_agent, locale, timezone_id):
        if pages:
            return await original(session, user_agent, locale, timezone_id)
        # The first request already captured its deadline. Give the subsequent
        # cold restart enough time, including on slow CI machines.
        monkeypatch.setattr(settings, "TOKEN_GENERATION_TIMEOUT_SECONDS", 120)
        browser = await session.get_browser()
        context = await browser.new_context()
        try:
            page = await context.new_page()
            pages.append(page)
            await page.evaluate("window.blocked = false")
            started.set()
            await page.evaluate("() => new Promise(resolve => { window.blocked = true; window.releaseToken = resolve; })")
            return "released-token"
        finally:
            await context.close()

    monkeypatch.setattr(generator, "_generate_token", generate)
    return started, pages


async def wait_for_blocked_page(started, pages):
    await asyncio.wait_for(started.wait(), 10)
    await pages[0].wait_for_function("window.blocked === true")


async def test_timeout_does_not_lose_queued_requests(token_generator, monkeypatch):
    await token_generator.get_token()
    old_session = token_generator._session
    started, pages = await block_first_token(token_generator, monkeypatch)
    monkeypatch.setattr(settings, "TOKEN_GENERATION_TIMEOUT_SECONDS", 1)
    first = asyncio.create_task(token_generator.get_token())
    await wait_for_blocked_page(started, pages)
    queued = [asyncio.create_task(token_generator.get_token()) for _ in range(2)]
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(first, 15)
    tokens = await asyncio.wait_for(asyncio.gather(*queued), 15)
    for token in tokens:
        verify_token_format(token)
    assert len(set(tokens)) == 2
    assert token_generator._session is not old_session


async def test_recovers_when_driver_dies_during_token(token_generator, monkeypatch):
    await token_generator.get_token()
    started, pages = await block_first_token(token_generator, monkeypatch)
    request = asyncio.create_task(token_generator.get_token())
    await wait_for_blocked_page(started, pages)
    driver_process(token_generator).kill()
    with pytest.raises(Exception):
        await asyncio.wait_for(request, 15)
    verify_token_format(await token_generator.get_token())


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="requires SIGSTOP")
async def test_timeout_recovers_from_frozen_driver(token_generator, monkeypatch):
    await token_generator.get_token()
    started, pages = await block_first_token(token_generator, monkeypatch)
    monkeypatch.setattr(settings, "TOKEN_GENERATION_TIMEOUT_SECONDS", 1)
    request = asyncio.create_task(token_generator.get_token())
    await wait_for_blocked_page(started, pages)
    process = driver_process(token_generator)
    process.send_signal(signal.SIGSTOP)
    try:
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(request, 25)
        assert process.returncode is not None
        verify_token_format(await token_generator.get_token())
    finally:
        if process.returncode is None:
            process.kill()


async def test_cancelling_request_keeps_browser_serialized(token_generator, monkeypatch):
    await token_generator.get_token()
    started, pages = await block_first_token(token_generator, monkeypatch)
    first = asyncio.create_task(token_generator.get_token())
    await wait_for_blocked_page(started, pages)
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    second = asyncio.create_task(token_generator.get_token())
    await asyncio.sleep(0.05)
    assert not second.done()
    assert len(token_generator._session.browser.contexts) == 1
    await pages[0].evaluate("window.releaseToken()")
    verify_token_format(await asyncio.wait_for(second, 15))
    assert token_generator._session.browser.contexts == []


async def test_close_fails_active_and_queued_requests(token_generator, monkeypatch):
    await token_generator.get_token()
    process = driver_process(token_generator)
    started, pages = await block_first_token(token_generator, monkeypatch)
    first = asyncio.create_task(token_generator.get_token())
    await wait_for_blocked_page(started, pages)
    queued = asyncio.create_task(token_generator.get_token())
    await asyncio.wait_for(token_generator.close(), 15)
    results = await asyncio.gather(first, queued, return_exceptions=True)
    assert all(isinstance(result, RuntimeError) for result in results)
    assert not token_generator._requests
    assert process.returncode is not None
    await token_generator.close()
    with pytest.raises(RuntimeError, match="closed"):
        await token_generator.get_token()


async def test_parallel_requests_are_unique_and_leave_no_contexts(token_generator):
    tokens = await asyncio.gather(*(token_generator.get_token() for _ in range(8)))
    assert len(set(tokens)) == 8
    for token in tokens:
        verify_token_format(token)
    assert token_generator._session.browser.contexts == []


async def test_late_launch_is_closed_before_replacement(token_generator, monkeypatch):
    module = importlib.import_module("apps.token.TokenGenerator")
    original_playwright = module.async_playwright
    release = asyncio.Event()
    browser = Mock(close=AsyncMock())

    async def late_launch(**kwargs):
        await release.wait()
        return browser

    playwright = Mock(chromium=Mock(launch=late_launch))
    manager = Mock(start=AsyncMock(return_value=playwright))
    manager.__aexit__ = AsyncMock(side_effect=lambda: release.set())
    monkeypatch.setattr(module, "async_playwright", lambda: manager)
    monkeypatch.setattr(settings, "TOKEN_GENERATION_TIMEOUT_SECONDS", 0.05)
    with pytest.raises(TimeoutError):
        await token_generator.get_token()
    browser.close.assert_awaited_once()
    assert token_generator._session is None
    assert not token_generator._closed
    monkeypatch.setattr(module, "async_playwright", original_playwright)
    monkeypatch.setattr(settings, "TOKEN_GENERATION_TIMEOUT_SECONDS", 120)
    verify_token_format(await token_generator.get_token())
